import shlex

import pytest
from helpers import get_ingress_url
from pytest_operator.plugin import OpsTest

USERNAME = "admin"
PASSWORD = "secret"


@pytest.mark.abort_on_fail
@pytest.mark.deploy
async def test_deploy_1dot6(ops_test: OpsTest, lightkube_client, deploy_cmd):
    print(f"Deploying bundle to {ops_test.model_full_name} using cmd '{deploy_cmd}'")
    rc, stdout, stderr = await ops_test.run(*shlex.split(deploy_cmd))

    print("Waiting for bundle to be ready")
    await ops_test.model.wait_for_idle(
        status="active",
        raise_on_blocked=False,
        raise_on_error=True,
        timeout=3000,
    )
    url = get_ingress_url(lightkube_client, ops_test.model_name)

    print("Update Dex and OIDC configs")
    await ops_test.model.applications["dex-auth"].set_config(
        {"public-url": url, "static-username": USERNAME, "static-password": PASSWORD}
    )
    await ops_test.model.applications["oidc-gatekeeper"].set_config({"public-url": url})

    await ops_test.model.wait_for_idle(
        status="active",
        raise_on_blocked=False,
        raise_on_error=True,
        timeout=600,
    )
