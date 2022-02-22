import logging
import inspect
from ipaddress import ip_address
from shutil import which
from subprocess import check_output
import time
from typing import Callable
import yaml

from kfp import Client
import lightkube
from lightkube import codecs
from lightkube.generic_resource import create_global_resource
from lightkube.models.meta_v1 import ObjectMeta
import pytest

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


# Helpers
@pytest.fixture(scope="session")
def lightkube_client() -> lightkube.Client:
    """Yields a lightkube client and generic resources (custom CRDs)."""
    client = lightkube.Client()
    global_resources = {
        "Profile": create_global_resource(
            group="kubeflow.org", version="v1", kind="Profile", plural="profiles"
        ),
    }
    return client, global_resources


@pytest.fixture(scope="session")
def profile(lightkube_client, request):
    """Creates a Profile object in cluster, cleaning it up after."""
    client, global_resources = lightkube_client

    username, profile_name = _get_user_identity_from_args(request)
    template_context = dict(profile_name=profile_name, username=username)
    profile = _load_profile_from_template(context=template_context)
    client.create(profile, profile_name)

    # Sleep to let the profile controller generate objects associated with profile
    # TODO: Should I watch for something to come up here?
    time.sleep(5)

    yield profile

    # Clean up after
    client.delete(global_resources["Profile"], profile_name)


def _get_user_identity_from_args(request):
    username = request.config.option.username
    profile_name = username.split("@")[0]
    return username, profile_name


def _load_profile_from_template(context):
    template_file = "tests/profile_template.yaml"
    with open(template_file) as f:
        objs = codecs.load_all_yaml(f, context=context)
    if len(objs) > 1:
        raise ValueError(f"Expected one object in profile yaml, found {len(objs)}")
    return objs[0]


@pytest.mark.parametrize(
    'name,fn',
    [
        # TODO: Move this to pipelines bundle
        # # TODO: Fix this test
        # pytest.param(
        #     'mnist',
        #     mnist_pipeline,
        #     marks=[pytest.mark.full, pytest.mark.lite],
        # ),
        # TODO: Move this to pipelines bundle
        pytest.param(
            'cowsay',
            cowsay_pipeline,
            marks=[pytest.mark.full, pytest.mark.lite],
        ),
        # # TODO: Move this to Katib bundle?
        # pytest.param(
        #     'katib',
        #     katib_pipeline,
        #     marks=[pytest.mark.full],
        # ),
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
def test_pipelines(name: str, fn: Callable, request, profile):
    """Runs each pipeline that it's been parameterized for, and waits for it to succeed."""

    # TODO: Make this an argument in CI
    kf_url = _get_kf_url()

    username = request.config.option.username
    password = request.config.option.password
    if username is None or password is None:
        raise ValueError(
            "Must specify username and password for testing.  Pass through pytest "
            "using --username and --password arguments"
        )
    namespace = username.split("@")[0]

    # kubeflow login credentials inferred from

    cookies = (
        f"authservice_session={kubeflow_login(host=kf_url, username=username, password=password)}"
    )

    host = f"{kf_url}/pipeline"
    client = Client(host=host, namespace=namespace, cookies=cookies)
    run = client.create_run_from_pipeline_func(fn, arguments=get_params(fn), namespace=namespace)
    completed = client.wait_for_run_completion(run.run_id, timeout=3600)
    status = completed.to_dict()['run']['status']
    assert status == 'Succeeded', f'Pipeline {name} status is {status}'
