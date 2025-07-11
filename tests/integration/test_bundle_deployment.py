import subprocess
import json
import os

import aiohttp
import lightkube
import pytest
import requests
from pytest_operator.plugin import OpsTest
from lightkube.resources.core_v1 import Service

BUNDLE_NAME = "kubeflow"

@pytest.fixture()
def lightkube_client() -> lightkube.Client:
    client = lightkube.Client(field_manager=BUNDLE_NAME)
    return client

@pytest.fixture
def bundle_path() -> str:
    return os.environ.get("BUNDLE_PATH").replace("\"", "")

class TestCharm:
    @pytest.mark.abort_on_fail
    async def test_bundle_deployment_works(self, ops_test: OpsTest, lightkube_client, bundle_path):
        subprocess.Popen(["juju", "deploy", bundle_path, "--trust"])

        # Wait for istio-ingressgateway charm to be active and idle
        # This is required because later we'll try to fetch a response from the login url
        # using the ingress gateway service IP address (provided by the LoadBalancer)
        await ops_test.model.wait_for_idle(
            apps=["istio-ingressgateway"],
            status="active",
            raise_on_blocked=False,
            raise_on_error=False,
            timeout=1500,
        )

        # Wait for the whole bundle to become active and idle
        await ops_test.model.wait_for_idle(
            status="active",
            raise_on_blocked=False,
            raise_on_error=False,
            timeout=1500,
        )

        url = get_public_url(lightkube_client, BUNDLE_NAME)
        result_status, result_text = await fetch_response(url)
        assert result_status == 200
        assert "Log in to Your Account" in result_text
        assert "Email Address" in result_text
        assert "Password" in result_text

def get_public_url(lightkube_client: lightkube.Client, bundle_name: str):
    """Extracts public url from service istio-ingressgateway-workload for EKS deployment.
    As a next step, this could be generalized in order for the above test to run in MicroK8s as well.
    """
    ingressgateway_svc = lightkube_client.get(
        Service, "istio-ingressgateway-workload", namespace=bundle_name
    )
    address = ingressgateway_svc.status.loadBalancer.ingress[0].hostname or ingressgateway_svc.status.loadBalancer.ingress[0].ip
    public_url = f"http://{address}"
    return public_url

async def fetch_response(url, headers=None):
    """Fetch provided URL and return pair - status and text (int, string)."""
    result_status = 0
    result_text = ""
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, headers=headers) as response:
            result_status = response.status
            result_text = await response.text()
    return result_status, str(result_text)
