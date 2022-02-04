import logging
import inspect
from ipaddress import ip_address
from shutil import which
from subprocess import check_output
from typing import Callable
import yaml

import pytest
from kfp import Client

from .pipelines.cowsay import cowsay_pipeline
from .pipelines.jupyter import jupyter_pipeline
from .pipelines.katib import katib_pipeline
from .pipelines.mnist import mnist_pipeline
from .pipelines.object_detection import object_detection_pipeline
from .kf_authentication import kubeflow_login


def get_params(func):
    return {name: value.default for name, value in inspect.signature(func).parameters.items()}


def _get_kf_url():
    juju = which('juju')
    if juju is None:
        juju = which('microk8s.juju')
    if juju is None:
        raise Exception("Juju not found!")

    status = yaml.safe_load(check_output([juju, 'status', '--format=yaml']))
    endpoint = status['applications']['istio-ingressgateway']['address']
    try:
        ip_address(endpoint)
        endpoint += '.nip.io'
    except ValueError:
        pass
    return f'http://{endpoint}/'


@pytest.mark.parametrize(
    'name,fn',
    [
        # TODO: Move this to pipelines bundle
        # # TODO: Fix this test
        # pytest.param(
        #     'mnist',
        #     mnist_pipeline,
        #     marks=[pytest.mark.full, pytest.mark.lite, pytest.mark.edge],
        # ),
        # TODO: Move this to pipelines bundle
        pytest.param(
            'cowsay',
            cowsay_pipeline,
            marks=[pytest.mark.full, pytest.mark.lite, pytest.mark.edge],
        ),
        # TODO: Move this to Katib bundle?
        pytest.param(
            'katib',
            katib_pipeline,
            marks=[pytest.mark.full],
        ),
        # pytest.param(
        #     'jupyter',
        #     jupyter_pipeline,
        #     marks=[pytest.mark.full, pytest.mark.lite],
        # ),
        pytest.param(
            'object_detection',
            object_detection_pipeline,
            marks=pytest.mark.gpu,
        ),
    ],
)
def test_pipelines(name: str, fn: Callable, request):
    """Runs each pipeline that it's been parameterized for, and waits for it to succeed."""

    # TODO: Make this an argument in CI
    kf_url = _get_kf_url()

    username = request.config.option.username
    password = request.config.option.password
    if username is None or password is None:
        raise ValueError("Must specify username and password for testing.  Pass through pytest "
                         "using --username and --password arguments")
    namespace = username.split("@")[0]

    # kubeflow login credentials inferred from

    cookies = f"authservice_session={kubeflow_login(host=kf_url, username=username, password=password)}"

    host = f"{kf_url}/pipeline"
    client = Client(host=host, namespace=namespace, cookies=cookies)
    run = client.create_run_from_pipeline_func(fn, arguments=get_params(fn), namespace=namespace)
    completed = client.wait_for_run_completion(run.run_id, timeout=3600)
    status = completed.to_dict()['run']['status']
    assert status == 'Succeeded', f'Pipeline {name} status is {status}'
