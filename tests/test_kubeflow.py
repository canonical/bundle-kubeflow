import re
from subprocess import check_output
from time import sleep

import pytest
import requests

from .utils import get_session, get_pub_addr

TFJOB = "integration/k8s-jobs/mnist.yaml"
SELDONJOB = "integration/k8s-jobs/serve-simple-v1alpha2.yml"


def kubectl_create(path: str):
    """Creates a Kubernetes resource from the given path.

    Uses juju kubectl plugin that introspects model and divines the proper
    kubeconfig.
    """

    return check_output(["juju", "kubectl", "--", "create", "-f", path]).strip()


def validate_statuses(model):
    """Validates that a known set of units have booted up into the correct state."""

    expected_units = {
        "ambassador-auth/0",
        "ambassador/0",
        "argo-controller/0",
        "argo-ui/0",
        "jupyter-controller/0",
        "jupyter-web/0",
        "jupyterhub/0",
        "katib-controller/0",
        "katib-manager/0",
        "katib-db/0",
        "katib-ui/0",
        "mariadb/0",
        "metacontroller/0",
        "minio/0",
        "modeldb-backend/0",
        "modeldb-store/0",
        "modeldb-ui/0",
        "pipelines-api/0",
        "pipelines-dashboard/0",
        "pipelines-persistence/0",
        "pipelines-scheduledworkflow/0",
        "pipelines-ui/0",
        "pipelines-viewer/0",
        "pytorch-operator/0",
        "redis/0",
        "seldon-api-frontend/0",
        "seldon-cluster-manager/0",
        "tensorboard/0",
        "tf-job-dashboard/0",
        "tf-job-operator/0",
    }

    assert set(model.units.keys()) == expected_units

    for name, unit in model.units.items():
        assert unit.agent_status == "idle"
        assert unit.workload_status == "active"
        assert unit.workload_status_message in ("", "ready")


def validate_ambassador():
    """Validates that the ambassador is up and responding."""

    checks = {
        "/ambassador/v0/check_ready": b"ambassador readiness check OK",
        "/ambassador/v0/check_alive": b"ambassador liveness check OK",
    }

    sess = get_session()

    for endpoint, text in checks.items():
        resp = sess.get(f"http://{get_pub_addr()}{endpoint}")
        assert resp.content.startswith(text)


def validate_jupyterhub_api():
    """Validates that JupyterHub is up and responding via Ambassador."""

    sess = get_session()

    resp = sess.get(f"http://{get_pub_addr()}/hub/api/")
    assert list(resp.json().keys()) == ["version"]


def validate_tf_dashboard():
    """Validates that TF Jobs dashboard is up and responding via Ambassador."""

    sess = get_session()

    output = kubectl_create(TFJOB)

    assert re.match(rb"tfjob.kubeflow.org/mnist-test-[a-z0-9]{5} created$", output) is not None

    expected_jobs = [("PS", 1), ("Worker", 1)]
    expected_conditions = [
        ("Created", "True", "TFJobCreated"),
        ("Running", "False", "TFJobRunning"),
        ("Succeeded", "True", "TFJobSucceeded"),
    ]
    expected_statuses = {"PS": {"succeeded": 1}, "Worker": {"succeeded": 1}}

    # Wait for up to 5 minutes for the job to complete,
    # checking every 5 seconds
    for i in range(60):
        resp = sess.get(f"http://{get_pub_addr()}/tfjobs/api/tfjob/")
        response = resp.json()["items"][0]

        jobs = [
            (name, spec["replicas"]) for name, spec in response["spec"]["tfReplicaSpecs"].items()
        ]

        conditions = [
            (cond["type"], cond["status"], cond["reason"])
            for cond in response["status"]["conditions"] or []
        ]

        statuses = response["status"]["replicaStatuses"]

        try:
            assert jobs == expected_jobs
            assert conditions == expected_conditions
            assert expected_statuses == statuses
            break
        except AssertionError as err:
            print("Waiting for TFJob to complete...")
            print(err)
            sleep(5)
    else:
        pytest.fail("Waited too long for TFJob to succeed!")


def validate_seldon():
    sess = get_session()

    output = kubectl_create(SELDONJOB)

    assert output == b"seldondeployment.machinelearning.seldon.io/mock-classifier created"

    for i in range(60):
        try:
            resp = sess.get(f"http://{get_pub_addr()}/seldon/mock-classifier/")
            resp.raise_for_status()
            assert resp.text == "Hello World!!"
            break
        except (AssertionError, requests.HTTPError) as err:
            print("Waiting for SeldonDeployment to start...")
            print(err)
            sleep(5)
    else:
        pytest.fail("Waited too long for SeldonDeployment to start!")
