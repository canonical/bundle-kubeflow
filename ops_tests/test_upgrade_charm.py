import logging
import subprocess
import tempfile
import asyncio

from juju.errors import JujuError
import yaml

import pytest

log = logging.getLogger(__name__)


@pytest.mark.abort_on_fail
async def test_deploy_old_bundle(ops_test):
    await ops_test.model.deploy("cs:kubeflow")
    subprocess.run(
        [
            'juju',
            'kubectl',
            'patch',
            'role/istio-ingressgateway-operator',
            '-p',
            yaml.dump(
                {
                    "apiVersion": "rbac.authorization.k8s.io/v1",
                    "kind": "Role",
                    "metadata": {"name": "istio-ingressgateway-operator"},
                    "rules": [{"apiGroups": ["*"], "resources": ["*"], "verbs": ["*"]}],
                }
            ),
        ]
    )
    # raise_on_error=False due to kubeflow-profiles going to an error state if
    # kubeflow-dashboard CRDs aren't created yet.
    await ops_test.model.wait_for_idle(raise_on_error=False)


async def test_upgrade_apps_in_bundle(ops_test):
    res = subprocess.run(["charm", "-v"])
    if res.returncode != 0:
        logging.error(
            "Charm snap is not installed, please install with: \n \
                sudo snap install charm --classic"
        )

    with tempfile.TemporaryDirectory() as temp_dir:
        bundle_dir = f"{temp_dir}/kubeflow-bundle"

        res = subprocess.run(["charm", "pull", "cs:kubeflow", "--channel", "edge", bundle_dir])

        with open(f"{bundle_dir}/bundle.yaml") as bundle_file:
            bundle = yaml.safe_load(bundle_file)

    for application, app_details in bundle["applications"].items():
        try:
            app = ops_test.model.applications[application]
            await app.refresh(switch=app_details["charm"])
        except JujuError as error:
            if "already running charm" in error.message:
                logging.info(f"{application} already using latest charm")
            else:
                raise error
    await ops_test.model.wait_for_idle()


async def test_status(ops_test):
    try:
        await ops_test.model.block_until(
            lambda: all(
                (unit.workload_status == "active") and unit.agent_status == "idle"
                for _, application in ops_test.model.applications.items()
                for unit in application.units
            ),
            timeout=600,
        )
    except asyncio.TimeoutError:
        assert False, "Test status timed out"
