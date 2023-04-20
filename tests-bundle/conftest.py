import lightkube
import pytest
from _pytest.config.argparsing import Parser


def pytest_addoption(parser: Parser):
    parser.addoption(
        "--file",
        help="Path to bundle file to use as the template for tests.  This must include all charms"
        "built by this bundle, where the locally built charms will replace those specified. "
        "This is useful for testing this bundle against different external dependencies. "
        "e.g. ./releases/1.6/kubeflow-bundle.yaml",
    )

    parser.addoption(
        "--channel",
        help="Kubeflow channels, e.g. latest/stable, 1.6/beta",
    )


@pytest.fixture(scope="module")
def lightkube_client(ops_test):
    yield lightkube.Client(namespace=ops_test.model_name, trust_env=False)


@pytest.fixture(scope="module")
def deploy_cmd(request, ops_test):
    if ops_test.model_name != "kubeflow":
        raise ValueError("kfp must be deployed to namespace kubeflow")

    bundle_file = request.config.getoption("file", default=None)
    channel = request.config.getoption("channel", default=None)

    if (not bundle_file and not channel) or (bundle_file and channel):
        raise ValueError("One of --file or --channel is required")

    model = ops_test.model_full_name
    if bundle_file:
        # pytest automatically prune path to relative paths without `./`
        # juju deploys requires `./`
        cmd = f"juju deploy ./{bundle_file} -m {model} --trust "
    elif channel:
        cmd = f"juju deploy kubeflow -m {model} --trust --channel {channel}"

    yield cmd
