# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
import subprocess

import tenacity
from lightkube import Client
from lightkube.resources.batch_v1 import Job
from lightkube.resources.core_v1 import Namespace

log = logging.getLogger(__name__)


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

    log.info(f"Waiting for namespace {namespace} to become 'Active': phase == {phase}")
    assert phase == "Active", f"Waited too long for namespace {namespace}!"


def _log_before_sleep(retry_state):
    """Custom callback to log the number of seconds before the next attempt."""
    next_attempt = retry_state.attempt_number
    delay = retry_state.next_action.sleep
    log.info(f"Retrying in {int(delay)} seconds (attempts: {next_attempt})")


@tenacity.retry(
    wait=tenacity.wait_exponential(multiplier=2, min=1, max=32),
    retry=tenacity.retry_if_not_result(lambda result: result),
    stop=tenacity.stop_after_delay(60 * 60),
    before_sleep=_log_before_sleep,
    reraise=True,
)
def wait_for_job(
    client: Client,
    job_name: str,
    namespace: str,
):
    """Wait for a Kubernetes Job to complete.

    Keep retrying (up to a maximum of 3600 seconds) while the Job is active or just not yet ready,
    and stop once it becomes successful. This is implemented using the built-in
    `retry_if_not_result` tenacity function, along with `wait_for_job` returning False or True,
    respectively.

    If the Job fails or lands in an unexpected state, this function will raise a ValueError and
    fail immediately.
    """
    # raises a 404 ApiError if the Job doesn't exist
    job = client.get(Job, name=job_name, namespace=namespace)
    if job.status.succeeded:
        # stop retrying, Job succeeded
        log.info(f"Job {namespace}/{job_name} completed successfully!")
        return True
    elif job.status.failed:
        raise ValueError(f"Job {namespace}/{job_name} failed!")
    elif not job.status.ready or job.status.active:
        # continue retrying
        status = "active" if job.status.active else "not ready"
        log.info(f"Waiting for Job {namespace}/{job_name} to complete (status == {status})")
        return False
    else:
        raise ValueError(f"Unknown status {job.status} for Job {namespace}/{job_name}!")


def fetch_job_logs(job_name, namespace):
    """Fetch the logs produced by a Kubernetes Job."""
    command = ["kubectl", "logs", "-n", namespace, f"job/{job_name}"]
    subprocess.check_call(command)


def delete_job(job_name, namespace, lightkube_client=None):
    """Delete a Kubernetes Job."""
    client = lightkube_client or Client()
    client.delete(Job, name=job_name, namespace=namespace)
