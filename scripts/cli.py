import json
import os
import random
import string
import subprocess
import sys
import tempfile
import textwrap
import time
from glob import glob
from pathlib import Path
from typing import Optional

import click
import yaml


DEFAULT_CONTROLLERS = {'microk8s': 'uk8s', 'aws': 'cdkkf'}


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
    return subprocess.run(
        args, check=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).stdout


def juju(*args, env=None):
    run('juju', *args, env=env)


def juju_debug(*args, env=None):
    run('juju', '--debug', *args, env=env)


#############
# UTILITIES #
#############


def _info(controller: str, model: str):
    pub_ip = get_pub_addr(None, controller, model)

    print(
        textwrap.dedent(
            f"""

        The central dashboard is available at http://{pub_ip}/

        To display the login credentials, run these commands:

            juju config ambassador-auth username
            juju config ambassador-auth password

        To tear down Kubeflow and associated infrastructure, run this command:

            python3 scripts/cli.py remove-from {controller}

        For more information, see documentation at:

        https://github.com/juju-solutions/bundle-kubeflow/blob/master/README.md

        """
        )
    )


def _subtrate_info_microk8s(model):
    print(
        textwrap.dedent(
            f"""
        Run `microk8s.kubectl proxy` to be able to access the dashboard at

        http://localhost:8001/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/#!/overview?namespace={model}
        """
        )
    )


def _subtrate_info_cdk(controller):
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

            {dashboard}/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/#!/overview

        The username and password are:

            {username}
            {password}

        To deploy Kubeflow on top of CDK, run `juju kubeflow deploy-to {controller}`.

        To tear down CDK and associated infrastructure, run this command:

            python3 scripts/cli.py cdk teardown

        For more information, see documentation at:

        https://github.com/juju-solutions/bundle-kubeflow/blob/master/README.md

        """
        )
    )


def get_pub_ip(controller: str, model: str):
    try:
        status = json.loads(
            get_output('juju', 'status', '-m', f'{controller}:default', '--format=json')
        )
        return status['applications']['kubernetes-worker']['units']['kubernetes-worker/0'][
            'public-address'
        ]
    except Exception as err:
        status = json.loads(
            get_output('juju', 'status', '-m', f'{controller}:{model}', '--format=json')
        )
        return status['applications']['ambassador']['units']['ambassador/0']['address']


def get_pub_addr(cloud: Optional[str], controller: str, model: str):
    if cloud == 'microk8s':
        return 'localhost'
    else:
        return f'{get_pub_ip(controller, model)}.xip.io'


def get_random_pass():
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
    password_overlay = {
        "applications": {
            "ambassador-auth": {"options": {"password": password}},
            "katib-db": {"options": {"root_password": get_random_pass()}},
            "modeldb-db": {"options": {"root_password": get_random_pass()}},
            "pipelines-db": {"options": {"root_password": get_random_pass()}},
            "pipelines-api": {"options": {"minio-secret-key": "minio123"}},
        }
    }

    start = time.time()

    if not cloud:
        clouds = json.loads(get_output('juju', 'list-clouds', '-c', controller, '--format=json'))
        clouds = [name for name, details in clouds.items() if details['type'] == 'k8s']
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
            juju('bundle', 'deploy', '--build', '--', *overlays)
        else:
            juju('deploy', 'kubeflow', '--channel', channel, *overlays)

    juju('wait', '-wv')

    # General Kubernetes setup.
    resources = Path(os.path.realpath(__file__)).parent / '../charms/*/resources/*.yaml'
    for f in glob(str(resources)):
        juju('kubectl', 'apply', '-f', f)

    pub_addr = get_pub_addr(cloud, controller, model)
    juju('config', 'ambassador', f'juju-external-hostname={pub_addr}')
    juju('expose', 'ambassador')

    end = time.time()

    click.secho(
        f'\nCongratulations, Kubeflow is now available. Took {int(end - start)} seconds.',
        color='green',
    )

    _info(controller, model)


@cli.command()
@click.argument('CONTROLLER')
@click.option('--model', default='kubeflow')
def info(controller, model):
    _info(controller, model)


@cli.command(name='remove-from')
@click.argument('CONTROLLER')
@click.option('--model', default='kubeflow')
@click.option('--purge/--no-purge', default=False)
def remove_from(controller, model, purge):
    args = ['destroy-model', f'{controller}:{model}']

    if purge:
        args += [f'--yes', '--destroy-storage', '--force']

    juju(*args)


@cli.group()
def microk8s():
    pass


@microk8s.command()
@click.option('--controller')
@click.option('-s', '--services', default=['dns', 'storage', 'dashboard'], multiple=True)
@click.option('--model-defaults', default=[], multiple=True)
def setup(controller, services, model_defaults):
    if not controller:
        controller = DEFAULT_CONTROLLERS['microk8s']

    for service in services:
        click.secho(f'Running microk8s.enable {service}', fg='green')
        run('microk8s.enable', service)
        for _ in range(12):
            try:
                get_output('microk8s.status', '--wait_ready')
                break
            except subprocess.CalledProcessError:
                click.echo('Waiting for microk8s to become ready...')
                time.sleep(5)
        else:
            click.secho(f'Couldn\'t enable {service}!', _fg='red')
            sys.exit(1)
        click.echo('\n')

    model_defaults = [f'--model-default={md}' for md in model_defaults]

    juju('bootstrap', 'microk8s', controller, *model_defaults)


@microk8s.command()
def info():
    _subtrate_info_microk8s('kubeflow')


@microk8s.command()
@click.option('--controller')
@click.option('--purge/--no-purge', default=False)
def teardown(controller, purge):
    if not controller:
        controller = DEFAULT_CONTROLLERS['microk8s']

    args = ['destroy-controller', controller]

    if purge:
        args += [f'--yes', '--destroy-all-models', '--destroy-storage']

    juju(*args)


@cli.group()
def cdk():
    pass


@cdk.command()
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
        'overlays/cdk.yml',
        '--overlay',
        f'overlays/cdk-{cloud}.yml',
    ]

    if gpu:
        deploy_args += ['--overlay', 'overlays/cdk-gpu.yml']

    # Spin up CDK
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
            '--storage',
            'juju-operator-storage',
            env={'KUBECONFIG': kubeconfig.name},
        )

    end = time.time()

    print(f'\nCongratulations, CDK is now available. Took {int(end - start)} seconds.')

    _subtrate_info_cdk(controller)


@cdk.command()
@click.option('--controller', default='cdkkf')
def info(controller):
    _subtrate_info_cdk(controller)


@cdk.command()
@click.option('--controller')
@click.option('--purge/--no-purge', default=False)
def teardown(controller, purge):
    if not controller:
        controller = DEFAULT_CONTROLLERS['aws']

    args = ['destroy-controller', controller]

    if purge:
        args += ['--yes', '--destroy-all-models', '--destroy-storage']

    juju(*args)


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
