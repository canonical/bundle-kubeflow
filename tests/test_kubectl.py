"""Runs tests by inspecting microk8s with kubectl."""

import pytest
import yaml
from sh import Command
from pytest_operator.plugin import OpsTest

try:
    from sh import juju_kubectl as kubectl
except ImportError:
    kubectl = Command('kubectl').bake('-nkubeflow')


def get_statuses():
    """Gets names and statuses of all workload pods.

    Uses Juju 2.8 label first, and if that's empty, tries Juju 2.9 label
    """

    pods = yaml.safe_load(kubectl.get('pods', '-ljuju-app', '-oyaml').stdout)

    if pods['items']:
        return {i['metadata']['labels']['juju-app']: i['status']['phase'] for i in pods['items']}
    else:
        pods = yaml.safe_load(kubectl.get('pods', '-lapp.kubernetes.io/name', '-oyaml').stdout)
        return {
            i['metadata']['labels']['app.kubernetes.io/name']: i['status']['phase']
            for i in pods['items']
        }


@pytest.mark.full
@pytest.mark.lite
async def test_all_charms_running(ops_test: OpsTest):
    await ops_test.model.wait_for_idle(
        status="active",
        raise_on_blocked=True,
        timeout=300,
    )


@pytest.mark.full
def test_crd_created_full():
    crds = yaml.safe_load(kubectl.get('crd', '-oyaml').stdout)

    names = {i['metadata']['name'] for i in crds['items']}
    assert names.issuperset(
        {
            'experiments.kubeflow.org',
            'notebooks.kubeflow.org',
            'poddefaults.kubeflow.org',
            'profiles.kubeflow.org',
            'scheduledworkflows.kubeflow.org',
            'seldondeployments.machinelearning.seldon.io',
            'servicerolebindings.rbac.istio.io',
            'serviceroles.rbac.istio.io',
            'suggestions.kubeflow.org',
            'trials.kubeflow.org',
            'viewers.kubeflow.org',
            'workflows.argoproj.io',
            'xgboostjobs.kubeflow.org',
            'mxjobs.kubeflow.org',
            'pytorchjobs.kubeflow.org',
            'tfjobs.kubeflow.org',
        }
    )


@pytest.mark.lite
def test_crd_created_lite():
    crds = yaml.safe_load(kubectl.get('crd', '-oyaml').stdout)

    names = {i['metadata']['name'] for i in crds['items']}
    assert names.issuperset(
        {
            'notebooks.kubeflow.org',
            'poddefaults.kubeflow.org',
            'profiles.kubeflow.org',
            'scheduledworkflows.kubeflow.org',
            'seldondeployments.machinelearning.seldon.io',
            'servicerolebindings.rbac.istio.io',
            'serviceroles.rbac.istio.io',
            'viewers.kubeflow.org',
            'workflows.argoproj.io',
            'xgboostjobs.kubeflow.org',
            'mxjobs.kubeflow.org',
            'pytorchjobs.kubeflow.org',
            'tfjobs.kubeflow.org',
        }
    )
