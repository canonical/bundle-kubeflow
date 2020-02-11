import json
import os
import random
import string
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path

import click
import yaml

DEFAULT_CONTROLLERS = {'microk8s': 'uk8s', 'aws': 'ckkf'}


def juju(*args, env=None):
    run('juju', *args, env=env)


def juju_debug(*args, env=None):
    run('juju', '--debug', *args, env=env)


#############
# UTILITIES #
#############


def run(*args, env: dict = None, check=True):
    """Runs command and exits script gracefully on errors."""

    click.secho(f'+ {" ".join(args)}', color='green')

    if env is None:
        env = os.environ
    else:
        env = {**env, **os.environ}

    result = subprocess.run(args, env=env)

    if check:
        try:
            result.check_returncode()
        except subprocess.CalledProcessError as err:
            if result.stderr:
                click.secho(result.stderr.decode('utf-8'), color='red')
            click.secho(str(err), color='red')
            sys.exit(1)


def get_output(*args: str):
    """Gets output from subcommand without echoing stdout."""

    return subprocess.run(
        args, check=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).stdout


def wait_for(*args: str, wait_msg: str, fail_msg: str):
    """Waits for subcommand to run successfully, with timeout."""

    for _ in range(12):
        try:
            subprocess.run(
                args,
                check=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            break
        except subprocess.CalledProcessError:
            click.echo(wait_msg)
            time.sleep(5)
    else:
        click.secho(fail_msg, _fg='red')
        sys.exit(1)


def kubeflow_info(controller: str, model: str):
    """Displays info about the deploy Kubeflow instance."""

    pub_ip = get_pub_addr(controller)

    print(
        textwrap.dedent(
            f"""

        The central dashboard is available at http://{pub_ip}/

        To display the login credentials, run these commands:

            juju config dex-auth static-username
            juju config dex-auth static-password

        To tear down Kubeflow, run this command:

            # Run `juju destroy-model --help` for a full listing of options,
            # such as how to release storage instead of destroying it.
            juju destroy-model {controller}:{model} --destroy-storage

        For more information, see documentation at:

        https://github.com/juju-solutions/bundle-kubeflow/blob/master/README.md

        """
        )
    )


def microk8s_info(model):
    """Displays info about MicroK8s."""

    print(
        textwrap.dedent(
            f"""
        Run `microk8s.kubectl proxy` to be able to access the dashboard at

        http://localhost:8001/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/#!/overview?namespace={model}
        """
        )
    )


def ck_info(controller):
    """Displays info about Charmed Kubernetes."""

    config = json.loads(
        get_output('juju', 'kubectl', '-m', f'{controller}:default', 'config', 'view', '-ojson')
    )

    dashboard = config['clusters'][0]['cluster']['server']
    username = config['users'][0]['user']['username']
    password = config['users'][0]['user']['password']

    print(
        textwrap.dedent(
            f"""

        The Kubernetes dashboard is available at:

            {dashboard}/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/#!/overview

        The username and password are:

            {username}
            {password}

        To deploy Kubeflow on top of Charmed Kubernetes, run `python3 scripts/cli.py deploy-to {controller}`.

        To tear down Charmed Kubernetes and associated infrastructure, run this command:

            # Run `juju destroy-controller --help` for a full listing of options,
            # such as how to release storage instead of destroying it.
            juju destroy-controller {controller} --destroy-storage

        For more information, see documentation at:

        https://github.com/juju-solutions/bundle-kubeflow/blob/master/README.md

        """
        )
    )


def get_pub_addr(controller: str):
    """Gets the hostname that Ambassador will respond to.

    For local deployments such as MicroK8s, it's just `localhost`, otherwise
    we just use the xip.io service with the IP address.
    """

    try:
        status = json.loads(
            get_output('juju', 'status', '-m', f'{controller}:default', '--format=json')
        )
    except subprocess.CalledProcessError:
        return os.environ.get('KUBEFLOW_URL') or 'localhost'

    units = status['applications']['kubernetes-worker']['units']
    worker = list(sorted(units.items()))[0][1]
    return worker['public-address'] + '.xip.io'


def get_random_pass():
    """Generates decently long random password."""

    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=30))


#######
# CLI #
#######


@click.group()
@click.option('--debug/--no-debug', default=False)
def cli(debug):
    if debug:
        global juju
        juju = juju_debug


@cli.command(name='deploy-to')
@click.argument('CONTROLLER')
@click.option('--cloud')
@click.option('--model', default='kubeflow')
@click.option('--channel', default='stable')
@click.option('--build/--no-build', default=False)
@click.option('-o', '--overlays', multiple=True)
@click.password_option(
    envvar='KUBEFLOW_AUTH_PASSWORD', prompt='Enter a password to set for the Kubeflow dashboard'
)
def deploy_to(controller, cloud, model, channel, build, overlays, password):
    # Dynamically-generated overlay, since there isn't a better
    # way of generating random passwords.
    pub_addr = get_pub_addr(controller)
    password_overlay = {
        "applications": {
            "dex-auth": {
                "options": {
                    "public-url": f'http://{pub_addr}:80',
                    "static-username": "admin",
                    "static-password": password,
                }
            },
            "katib-db": {"options": {"root_password": get_random_pass()}},
            "modeldb-db": {"options": {"root_password": get_random_pass()}},
            "oidc-gatekeeper": {
                "options": {
                    "public-url": f'http://{pub_addr}:80',
                    "client-secret": get_random_pass(),
                }
            },
            "pipelines-api": {"options": {"minio-secret-key": "minio123"}},
            "pipelines-db": {"options": {"root_password": get_random_pass()}},
        }
    }

    start = time.time()

    # If a specific cloud wasn't passed in, try to figure out which one to use
    if not cloud:
        try:
            output = get_output('juju', 'list-clouds', '-c', controller, '--format=json', '--all')
        except subprocess.CalledProcessError as err:
            if err.stderr is not None:
                click.secho('STDERR: ' + err.stderr.decode('utf-8'), color='red')
            click.secho(str(err))
            sys.exit(1)
        clouds = [
            name
            for name, details in json.loads(output).items()
            if details['type'] == 'k8s' and details['defined'] == 'public'
        ]
        if not clouds:
            click.secho(f'No Kubernetes clouds found on controller {controller}', color='red')
            sys.exit(1)
        elif len(clouds) > 1:
            msg = (
                f'Multiple Kubernetes clouds found on controller {controller}: {" ".join(clouds)}'
                'Pick which one to use with `--cloud=foo`.'
            )
            click.secho(msg, color='red')
            sys.exit(1)
        else:
            cloud = clouds[0]

    juju('add-model', model, cloud)

    with tempfile.NamedTemporaryFile('w+') as f:
        overlays = [f'--overlay={o}' for o in overlays]

        yaml.dump(password_overlay, f)
        overlays.append(f'--overlay={f.name}')

        # Allow building local bundle.yaml, otherwise deploy from the charm store
        if build:
            juju('bundle', 'deploy', '--build', '--', '-m', model, *overlays)
        else:
            juju('deploy', '-m', model, 'kubeflow', '--channel', channel, *overlays)

    juju('wait', '-wv', '-m', model)

    juju('config', 'ambassador', f'juju-external-hostname={pub_addr}')
    juju('expose', 'ambassador')

    end = time.time()

    click.secho(
        f'\nCongratulations, Kubeflow is now available. Took {int(end - start)} seconds.',
        color='green',
    )

    kubeflow_info(controller, model)


@cli.command()
@click.argument('CONTROLLER')
@click.option('--model', default='kubeflow')
def info(controller, model):
    kubeflow_info(controller, model)


@cli.group()
def microk8s():
    pass


@microk8s.command()
@click.option('--controller')
@click.option('-s', '--services', default=['dns', 'storage', 'rbac', 'dashboard'], multiple=True)
@click.option('--model-defaults', default=[], multiple=True)
def setup(controller, services, model_defaults):
    if not controller:
        controller = DEFAULT_CONTROLLERS['microk8s']

    for service in services:
        click.secho(f'Running microk8s.enable {service}', fg='green')
        run('microk8s.enable', service)
        wait_for(
            'microk8s.status',
            '--wait-ready',
            wait_msg='Waiting for microk8s to become ready...',
            fail_msg=f'Couldn\'t enable {service}!',
        )
        click.echo('\n')

    model_defaults = [f'--model-default={md}' for md in model_defaults]

    wait_for(
        'microk8s.kubectl',
        'get',
        'StorageClass',
        'microk8s-hostpath',
        wait_msg='Waiting for storage to come up before bootstrapping',
        fail_msg='Waited too long for storage to come up!',
    )

    juju('bootstrap', 'microk8s', controller, *model_defaults)


@microk8s.command()
def info():
    microk8s_info('kubeflow')


@cli.group()
def ck():
    pass


@ck.command()
@click.option('--cloud', default='aws')
@click.option('--region', default='us-east-1')
@click.option('--controller')
@click.option('--channel', default='stable')
@click.option('--gpu/--no-gpu', default=False)
def setup(cloud, region, controller, channel, gpu):
    if not controller:
        controller = DEFAULT_CONTROLLERS[cloud]

    start = time.time()

    deploy_args = [
        'cs:bundle/canonical-kubernetes',
        '--trust',
        '--channel',
        channel,
        '--overlay',
        'overlays/ck.yml',
        '--overlay',
        f'overlays/ck-{cloud}.yml',
    ]

    if gpu:
        deploy_args += ['--overlay', 'overlays/ck-gpu.yml']

    # Spin up Charmed Kubernetes
    juju('bootstrap', f'{cloud}/{region}', controller)
    juju('deploy', *deploy_args)

    juju('wait', '-wv')

    juju('kubectl', 'apply', '-f', f'storage/{cloud}-ebs.yml')

    with tempfile.NamedTemporaryFile() as kubeconfig:
        # Copy details of cloud locally, and tell juju about it
        juju('scp', '-m', f'{controller}:default', 'kubernetes-master/0:~/config', kubeconfig.name)
        juju(
            'add-k8s',
            controller,
            '-c',
            controller,
            f'--region={cloud}/{region}',
            env={'KUBECONFIG': kubeconfig.name},
        )

    end = time.time()

    print(
        '\nCongratulations, Charmed Kubernetes is now available. '
        f'Took {int(end - start)} seconds.'
    )

    ck_info(controller)


@ck.command()
@click.option('--controller', default='ckkf')
def info(controller):
    ck_info(controller)


@cli.group()
def k8s():
    pass


@k8s.command()
@click.argument('NAME')
@click.option('--storage', required=True)
@click.option('--kubeconfig', default=Path('~/.kube/config').expanduser())
@click.option('--cloud')
@click.option('--region')
def add(name, storage, kubeconfig, cloud, region):
    args = ['add-k8s', name, '--storage', storage]

    if cloud:
        args += ['--cloud', cloud]

    if region:
        args += ['--region', region]

    juju(*args, env={'KUBECONFIG': kubeconfig})


@k8s.command()
@click.argument('NAME')
def remove(name):
    juju('remove-k8s', name)


if __name__ == '__main__':
    cli()
