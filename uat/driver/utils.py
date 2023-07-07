# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
import os
import shutil
import subprocess

import tenacity
from lightkube import Client
from lightkube.core.resource import Resource
from lightkube.resources.core_v1 import Namespace

logger = logging.getLogger(__name__)


@tenacity.retry(
    wait=tenacity.wait_exponential(multiplier=2, min=1, max=10),
    stop=tenacity.stop_after_attempt(30),
    reraise=True,
)
def assert_namespace_active(
    client: Client,
    namespace: str,
):
    """Test that the provided namespace is Active.

    Retries multiple times to allow for the K8s namespace to be created and reach Active status.
    """
    # raises a 404 ApiError if the namespace doesn't exist
    ns = client.get(Namespace, namespace)
    phase = ns.status.phase

    logger.info(f"Waiting for namespace {namespace} to become 'Active': phase == {phase}")
    assert phase == "Active", f"Waited too long for namespace {namespace}!"


@tenacity.retry(
    wait=tenacity.wait_exponential(multiplier=2, min=1, max=10),
    stop=tenacity.stop_after_attempt(30),
    reraise=True,
)
def assert_replicas(
    client: Client,
    resource_class: Resource,
    resource_name: str,
    namespace: str,
    target_replicas: int = 1,
):
    """Test for replicas.

    Retries multiple times to allow for K8s resource to reach the target number of ready replicas.
    """
    rsc = client.get(resource_class, resource_name, namespace=namespace)
    replicas = rsc.get("status", {}).get("readyReplicas")

    resource = f"{namespace}/{resource_class.__name__}/{resource_name}"
    logger.info(
        f"Waiting for {resource} to reach {target_replicas} ready replicas:"
        f" readyReplicas == {replicas}"
    )

    assert replicas == target_replicas, f"Waited too long for {resource}!"


def is_microk8s_cluster():
    """Check if the current cluster is a MicroK8s cluster."""
    return shutil.which("kubectl") is None


def copy_to_pod(pod_name, namespace, src_path, dst_path=None):
    """Copy a local file or directory to a Pod."""
    command = [
        "kubectl",
        "cp",
        src_path,
        f"{namespace}/{pod_name}:{dst_path or os.path.basename(src_path)}",
    ]
    if is_microk8s_cluster():
        command.insert(0, "microk8s")
    # execute the kubectl command and raise a CalledProcessError on failure
    subprocess.run(command, check=True)


def run_in_pod(pod_name, namespace, command):
    """Run a command in a Pod."""
    command = ["kubectl", "exec", "-n", namespace, pod_name, "--", "bash", "-c", *command]
    if is_microk8s_cluster():
        command.insert(0, "microk8s")
    # execute the kubectl command and capture the output
    return subprocess.run(command, capture_output=True, text=True)
    # print the captured output
    # print(result.stdout.decode())
    # print(result.stderr.decode())
