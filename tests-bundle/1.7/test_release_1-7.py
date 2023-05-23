import shlex

import pytest
from helpers import get_ingress_url, from_minutes
from pytest_operator.plugin import OpsTest

USERNAME = "admin"
PASSWORD = "admin"


@pytest.mark.abort_on_fail
@pytest.mark.deploy
async def test_deploy(ops_test: OpsTest, lightkube_client, deploy_cmd):
    print(f"Deploying bundle to {ops_test.model_full_name} using cmd '{deploy_cmd}'")
    rc, stdout, stderr = await ops_test.run(*shlex.split(deploy_cmd))

    if rc != 0:
        raise Exception(f"Deploy failed with code: {rc}, \nstdout: {stdout}, \nstderr {stderr}")

    print("Waiting for bundle to be ready")
    apps = [
        'admission-webhook',
        'argo-controller',
        'argo-server',
        'dex-auth',
        'istio-ingressgateway',
        'istio-pilot',
        'jupyter-controller',
        'jupyter-ui',
        'katib-controller',
        'katib-db',
        'katib-db-manager',
        'katib-ui',
        'kfp-api',
        'kfp-db',
        'kfp-persistence',
        'kfp-profile-controller',
        'kfp-schedwf',
        'kfp-ui',
        'kfp-viewer',
        'kfp-viz',
        'knative-eventing',
        'knative-operator',
        'knative-serving',
        'kserve-controller',
        'kubeflow-dashboard',
        'kubeflow-profiles',
        'kubeflow-roles',
        'kubeflow-volumes',
        'metacontroller-operator',
        'minio',
        # 'oidc-gatekeeper',  # this is expected to wait for public-url config
        'seldon-controller-manager',
        # 'tensorboard-controller',  # this is expected to wait for config
        'tensorboards-web-app',
        'training-operator',
    ]
    await ops_test.model.wait_for_idle(
        apps=apps,
        status="active",
        raise_on_blocked=False,
        raise_on_error=False,
        timeout=from_minutes(minutes=180),
    )
    print("All applications are active")

    url = get_ingress_url(lightkube_client, ops_test.model_name)

    print("Update Dex and OIDC configs")
    await ops_test.model.applications["dex-auth"].set_config(
        {"public-url": url, "static-username": USERNAME, "static-password": PASSWORD}
    )
    await ops_test.model.applications["oidc-gatekeeper"].set_config({"public-url": url})

    # append apps since they should be configured now
    apps.append("oidc-gatekeeper")
    await ops_test.model.wait_for_idle(
        apps=apps,
        status="active",
        raise_on_blocked=False,
        raise_on_error=False,
        timeout=from_minutes(minutes=100),
    )

    print("dispatch istio config changed hook")
    rc, stdout, stderr = await ops_test.run(
        *shlex.split(
            'juju run --unit istio-pilot/0 -- "export JUJU_DISPATCH_PATH=hooks/config-changed; ./dispatch"'
        )
    )

    if rc != 0:
        raise Exception(f"Dispatch failed with code: {rc}, \nstdout: {stdout}, \nstderr {stderr}")

    # now wait for all apps
    await ops_test.model.wait_for_idle(
        status="active",
        raise_on_blocked=False,
        raise_on_error=True,
        timeout=from_minutes(minutes=30),
        idle_period=from_minutes(minutes=3),
    )
