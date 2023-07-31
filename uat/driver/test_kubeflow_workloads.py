# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
import os
from pathlib import Path

import pytest
from lightkube import ApiError, Client, codecs
from lightkube.generic_resource import create_global_resource, load_in_cluster_generic_resources
from utils import assert_namespace_active, delete_job, fetch_job_logs, wait_for_job

log = logging.getLogger(__name__)

ASSETS_DIR = Path("assets")
JOB_TEMPLATE_FILE = ASSETS_DIR / "test-job.yaml.j2"
PROFILE_TEMPLATE_FILE = ASSETS_DIR / "test-profile.yaml.j2"

TESTS_DIR = os.path.abspath(Path("integrations"))
TESTS_IMAGE = "kubeflownotebookswg/jupyter-scipy:v1.7.0"

NAMESPACE = "test-kubeflow"
PROFILE_RESOURCE = create_global_resource(
    group="kubeflow.org",
    version="v1",
    kind="profile",
    plural="profiles",
)

JOB_NAME = "test-kubeflow"


@pytest.fixture(scope="module")
def lightkube_client():
    """Initialise Lightkube Client."""
    lightkube_client = Client()
    load_in_cluster_generic_resources(lightkube_client)
    return lightkube_client


@pytest.fixture(scope="module")
def create_profile(lightkube_client):
    """Create Profile and handle cleanup at the end of the module tests."""
    log.info(f"Creating Profile {NAMESPACE}...")
    resources = list(
        codecs.load_all_yaml(
            PROFILE_TEMPLATE_FILE.read_text(),
            context={"namespace": NAMESPACE},
        )
    )
    assert len(resources) == 1, f"Expected 1 Profile, got {len(resources)}!"
    lightkube_client.create(resources[0])

    yield

    # delete the Profile at the end of the module tests
    log.info(f"Deleting Profile {NAMESPACE}...")
    lightkube_client.delete(PROFILE_RESOURCE, name=NAMESPACE)


@pytest.mark.abort_on_fail
async def test_create_profile(lightkube_client, create_profile):
    """Test Profile creation.

    This test relies on the create_profile fixture, which handles the Profile creation and
    is responsible for cleaning up at the end.
    """
    try:
        profile_created = lightkube_client.get(
            PROFILE_RESOURCE,
            name=NAMESPACE,
        )
    except ApiError as e:
        if e.status == 404:
            profile_created = False
        else:
            raise
    assert profile_created, f"Profile {NAMESPACE} not found!"

    assert_namespace_active(lightkube_client, NAMESPACE)


def test_kubeflow_workloads(lightkube_client):
    """Run a K8s Job to execute the notebook tests."""
    log.info(f"Starting Kubernetes Job {NAMESPACE}/{JOB_NAME} to run notebook tests...")
    resources = list(
        codecs.load_all_yaml(
            JOB_TEMPLATE_FILE.read_text(),
            context={"job_name": JOB_NAME, "test_dir": TESTS_DIR, "test_image": TESTS_IMAGE},
        )
    )
    assert len(resources) == 1, f"Expected 1 Job, got {len(resources)}!"
    lightkube_client.create(resources[0], namespace=NAMESPACE)

    try:
        wait_for_job(lightkube_client, JOB_NAME, NAMESPACE)
    except ValueError:
        pytest.fail(
            f"Something went wrong while running Job {NAMESPACE}/{JOB_NAME}. Please inspect the"
            " attached logs for more info..."
        )
    finally:
        log.info("Fetching Job logs...")
        fetch_job_logs(JOB_NAME, NAMESPACE)


def teardown_module():
    """Cleanup resources."""
    log.info(f"Deleting Job {NAMESPACE}/{JOB_NAME}...")
    delete_job(JOB_NAME, NAMESPACE)
