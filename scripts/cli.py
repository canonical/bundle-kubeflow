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
import shutil
from typing import Optional

import click
import yaml

DEFAULT_CONTROLLERS = {'microk8s': 'uk8s', 'aws': 'ckkf'}


def juju(*args, env=None, die=True):
    run('juju', *args, env=env, die=die)


def juju_debug(*args, env=None, die=True):
    run('juju', '--debug', *args, env=env, die=die)


#############
# UTILITIES #
#############


def check_for(name: str, snap_name: Optional[str] = None):
    if not shutil.which(name):
        print(f"\nCommand {name} not found.\n")
        print("Please run this command before running this script:\n")
        print(f"    sudo snap install {snap_name or name} --classic\n")
        sys.exit(1)


def run(*args, env: dict = None, check=True, die=True):
    """Runs command and exits script gracefully on errors."""

    click.secho(f'+ {" ".join(args)}', fg='green')

    if env is None:
        env = os.environ
    else:
        env = {**env, **os.environ}

    result = subprocess.run(args, env=env)

    if check:
        try:
            result.check_returncode()
        except subprocess.CalledProcessError as err:
            if die:
                if result.stderr:
                    click.secho(result.stderr.decode('utf-8'), fg='red')
                click.secho(str(err), fg='red')
                sys.exit(1)
            else:
                raise


def get_output(*args: str):
    """Gets output from subcommand without echoing stdout."""

    return subprocess.run(
        args, check=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
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
        click.secho(fail_msg, fg='red')
        sys.exit(1)


def kubeflow_info(controller: str, model: str):
    """Displays info about the deploy Kubeflow instance."""

    pub_addr = get_pub_addr(controller)

    print(
        textwrap.dedent(
            f"""

        The central dashboard is available at http://{pub_addr}/

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
    """Gets the hostname that Ambassador will respond to."""

    # Check if we've manually set a hostname on the ingress
    try:
        output = get_output('juju', 'kubectl', 'get', 'ingress/ambassador', '-ojson')
        return json.loads(output)['spec']['rules'][0]['host']
    except (KeyError, subprocess.CalledProcessError) as err:
        pass

    # Check if juju expose has created an ELB or similar
    try:
        output = get_output('juju', 'kubectl', 'get', 'svc/ambassador', '-ojson')
        return json.loads(output)['status']['loadBalancer']['ingress'][0]['hostname']
    except (KeyError, subprocess.CalledProcessError) as err:
        pass

    # Otherwise, see if we've set up metallb with a custom service
    try:
        output = get_output('juju', 'kubectl', 'get', 'svc/ambassador', '-ojson')
        pub_ip = json.loads(output)['status']['loadBalancer']['ingress'][0]['ip']
        return '%s.xip.io' % pub_ip
    except (KeyError, subprocess.CalledProcessError) as err:
        pass

    # If all else fails, just use localhost
    return 'localhost'


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
@click.option('--bundle', default='full')
@click.option('--channel', default='stable')
@click.option('--public-address')
@click.option('--build/--no-build', default=False)
@click.option('-o', '--overlays', multiple=True)
@click.password_option(
    envvar='KUBEFLOW_AUTH_PASSWORD', prompt='Enter a password to set for the Kubeflow dashboard',
)
def deploy_to(controller, cloud, model, bundle, channel, public_address, build, overlays, password):
    check_for('juju')
    if build:
        check_for('juju-bundle', snap_name='juju-helpers')
        check_for('charm')

    # Dynamically-generated overlay, since there isn't a better
    # way of generating random passwords.
    if bundle == 'full':
        bundle_yaml = 'bundle.yaml'
        bundle_url = 'kubeflow'
        password_overlay = {
            "applications": {
                "dex-auth": {"options": {"static-username": "admin", "static-password": password}},
                "katib-db": {"options": {"root_password": get_random_pass()}},
                "oidc-gatekeeper": {"options": {"client-secret": get_random_pass()}},
                "pipelines-api": {"options": {"minio-secret-key": "minio123"}},
                "pipelines-db": {"options": {"root_password": get_random_pass()}},
            }
        }
    elif bundle == 'lite':
        bundle_yaml = 'bundle-lite.yaml'
        bundle_url = 'kubeflow-lite'
        password_overlay = {
            "applications": {
                "dex-auth": {"options": {"static-username": "admin", "static-password": password}},
                "oidc-gatekeeper": {"options": {"client-secret": get_random_pass()}},
                "pipelines-api": {"options": {"minio-secret-key": "minio123"}},
                "pipelines-db": {"options": {"root_password": get_random_pass()}},
            }
        }
    elif bundle == 'edge':
        bundle_yaml = 'bundle-edge.yaml'
        bundle_url = 'kubeflow-edge'
        password_overlay = {
            "applications": {
                "pipelines-api": {"options": {"minio-secret-key": "minio123"}},
                "pipelines-db": {"options": {"root_password": get_random_pass()}},
            }
        }
    else:
        raise Exception(f"Unknown bundle {bundle}")

    start = time.time()

    # If a specific cloud wasn't passed in, try to figure out which one to use
    if not cloud:
        try:
            output = get_output('juju', 'list-clouds', '-c', controller, '--format=json', '--all')
        except subprocess.CalledProcessError as err:
            if err.stderr is not None:
                click.secho('STDERR: ' + err.stderr.decode('utf-8'), fg='red')
            click.echo(str(err))
            sys.exit(1)
        clouds = [
            name
            for name, details in json.loads(output).items()
            if details['type'] == 'k8s' and details['defined'] == 'public'
        ]
        if not clouds:
            click.secho(f'No Kubernetes clouds found on controller {controller}', fg='red')
            sys.exit(1)
        elif len(clouds) > 1:
            msg = (
                f'Multiple Kubernetes clouds found on controller {controller}: {" ".join(clouds)}'
                'Pick which one to use with `--cloud=foo`.'
            )
            click.secho(msg, fg='red')
            sys.exit(1)
        else:
            cloud = clouds[0]

    juju('add-model', model, cloud, '--config', 'logging-config="<root>=DEBUG;unit=DEBUG"')

    with tempfile.NamedTemporaryFile('w+') as f:
        overlays = [f'--overlay={o}' for o in overlays]

        yaml.dump(password_overlay, f)
        overlays.append(f'--overlay={f.name}')

        # Allow building local bundle.yaml, otherwise deploy from the charm store
        if build:
            juju('bundle', 'deploy', '-b', bundle_yaml, '--build', '--', '-m', model, *overlays)
        else:
            juju('deploy', bundle_url, '-m', model, '--channel', channel, *overlays)

    juju('wait', '-wv', '-m', model, '-t', str(15 * 60))

    if bundle in ('full', 'lite'):
        with tempfile.NamedTemporaryFile(mode='w+') as f:
            yaml.dump(
                {
                    'apiVersion': 'v1',
                    'kind': 'Service',
                    'metadata': {'labels': {'juju-app': 'pipelines-api'}, 'name': 'ml-pipeline'},
                    'spec': {
                        'ports': [
                            {'name': 'grpc', 'port': 8887, 'protocol': 'TCP', 'targetPort': 8887},
                            {'name': 'http', 'port': 8888, 'protocol': 'TCP', 'targetPort': 8888},
                        ],
                        'selector': {'juju-app': 'pipelines-api'},
                        'type': 'ClusterIP',
                    },
                },
                f,
            )
            juju('kubectl', 'apply', '-f', f.name)

    juju(
        "kubectl",
        "wait",
        f"--namespace={model}",
        "--for=condition=Ready",
        "pod",
        "--timeout=-1s",
        "--all",
    )

    if bundle == 'full':
        juju(
            'kubectl',
            'delete',
            'mutatingwebhookconfigurations/katib-mutating-webhook-config',
            'validatingwebhookconfigurations/katib-validating-webhook-config',
        )

    if bundle in ('full', 'lite'):
        pub_addr = public_address or get_pub_addr(controller)
        juju('config', 'dex-auth', f'public-url=http://{pub_addr}:80')
        juju('config', 'oidc-gatekeeper', f'public-url=http://{pub_addr}:80')

        juju('config', 'ambassador', f'juju-external-hostname={pub_addr}')
        juju('expose', 'ambassador')

    juju('wait', '-wv', '-m', model, '-t', str(10 * 60))

    end = time.time()

    click.secho(
        f'\nCongratulations, Kubeflow is now available. Took {int(end - start)} seconds.',
        fg='green',
    )

    kubeflow_info(controller, model)


@cli.command(name='upgrade')
@click.argument('CONTROLLER')
@click.option('--model', default='kubeflow')
@click.option('--bundle', default='full')
@click.option('--channel', default='stable')
@click.option('--build/--no-build', default=False)
def upgrade(controller, model, bundle, channel, build):
    check_for('juju')
    if build:
        check_for('juju-bundle', snap_name='juju-helpers')
        check_for('charm')

    if bundle == 'full':
        bundle_yaml = 'bundle.yaml'
        bundle_url = 'kubeflow'
    elif bundle == 'lite':
        bundle_yaml = 'bundle-lite.yaml'
        bundle_url = 'kubeflow-lite'
    elif bundle == 'edge':
        bundle_yaml = 'bundle-edge.yaml'
        bundle_url = 'kubeflow-edge'
    else:
        raise Exception(f"Unknown bundle {bundle}")

    start = time.time()

    # Allow building local bundle.yaml, otherwise deploy from the charm store
    if build:
        juju('bundle', 'deploy', '-b', bundle_yaml, '--build', '--', '-m', model)
    else:
        juju('deploy', bundle_url, '-m', model, '--channel', channel)

    juju('wait', '-wv', '-m', model)

    juju(
        "kubectl",
        "wait",
        f"--namespace={model}",
        "--for=condition=Ready",
        "pod",
        "--timeout=-1s",
        "--all",
    )

    end = time.time()

    click.secho(
        f'\nCongratulations, Kubeflow is now available. Took {int(end - start)} seconds.',
        fg='green',
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
@click.option(
    '-s',
    '--services',
    default=['dns', 'storage', 'dashboard', 'ingress', 'metallb:10.64.140.43-10.64.140.49'],
    multiple=True,
)
@click.option('--test-mode/--no-test-mode', default=False)
def setup(controller, services, test_mode):
    check_for('microk8s.enable', snap_name='microk8s')

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

    wait_for(
        "microk8s.kubectl",
        "wait",
        "--for=condition=available",
        "-nkube-system",
        "deployment/coredns",
        "deployment/hostpath-provisioner",
        "--timeout=10m",
        wait_msg='Waiting for DNS and storage plugins to finish setting up',
        fail_msg='Waited too long for addons to come up!',
    )

    args = []
    if test_mode:
        args += ['--config', 'test-mode=true', '--model-default', 'test-mode=true']
    juju('bootstrap', 'microk8s', '--debug', controller, *args)


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
@click.option('--test-mode/--no-test-mode', default=False)
@click.option('--gpu/--no-gpu', default=False)
def setup(cloud, region, controller, channel, test_mode, gpu):
    check_for('juju')
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
    args = []
    if test_mode:
        args += ['--config', 'test-mode=true', '--model-default', 'test-mode=true']
    juju('bootstrap', f'{cloud}/{region}', controller, *args)
    juju('deploy', *deploy_args)

    juju('wait', '-wv')

    with tempfile.NamedTemporaryFile() as kubeconfig:
        # Copy details of cloud locally, and tell juju about it
        juju(
            'scp', '-m', f'{controller}:default', 'kubernetes-master/0:~/config', kubeconfig.name,
        )
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
