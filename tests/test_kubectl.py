"""Runs tests by inspecting microk8s with kubectl."""

from time import sleep

import pytest
import yaml
from flaky import flaky
from sh import Command

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
@flaky(max_runs=60, rerun_filter=lambda *_: sleep(5) or True)
def test_running_full():
    assert get_statuses() == {
        'admission-webhook': 'Running',
        'argo-controller': 'Running',
        'dex-auth': 'Running',
        'istio-ingressgateway': 'Running',
        'istio-pilot': 'Running',
        'jupyter-controller': 'Running',
        'jupyter-ui': 'Running',
        'katib-controller': 'Running',
        'katib-db': 'Running',
        'katib-db-manager': 'Running',
        'katib-ui': 'Running',
        'kfp-api': 'Running',
        'kfp-db': 'Running',
        'kfp-persistence': 'Running',
        'kfp-schedwf': 'Running',
        'kfp-ui': 'Running',
        'kfp-viewer': 'Running',
        'kfp-viz': 'Running',
        'kubeflow-dashboard': 'Running',
        'kubeflow-profiles': 'Running',
        'kubeflow-volumes': 'Running',
        'minio': 'Running',
        'mlmd': 'Running',
        'oidc-gatekeeper': 'Running',
        'pytorch-operator': 'Running',
        'seldon-controller-manager': 'Running',
        'spark': 'Running',
        'tfjob-operator': 'Running',
    }


@pytest.mark.lite
@flaky(max_runs=60, rerun_filter=lambda *_: sleep(5) or True)
def test_running_lite():
    assert get_statuses() == {
        'admission-webhook': 'Running',
        'argo-controller': 'Running',
        'dex-auth': 'Running',
        'istio-ingressgateway': 'Running',
        'istio-pilot': 'Running',
        'jupyter-controller': 'Running',
        'jupyter-ui': 'Running',
        'kubeflow-dashboard': 'Running',
        'kubeflow-profiles': 'Running',
        'kubeflow-volumes': 'Running',
        'minio': 'Running',
        'mlmd': 'Running',
        'oidc-gatekeeper': 'Running',
        'kfp-api': 'Running',
        'kfp-db': 'Running',
        'kfp-persistence': 'Running',
        'kfp-schedwf': 'Running',
        'kfp-ui': 'Running',
        'kfp-viewer': 'Running',
        'kfp-viz': 'Running',
        'pytorch-operator': 'Running',
        'seldon-controller-manager': 'Running',
        'tfjob-operator': 'Running',
    }


@pytest.mark.edge
@flaky(max_runs=60, rerun_filter=lambda *_: sleep(5) or True)
def test_running_edge():
    assert get_statuses() == {
        'argo-controller': 'Running',
        'kfp-api': 'Running',
        'kfp-db': 'Running',
        'kfp-persistence': 'Running',
        'kfp-schedwf': 'Running',
        'minio': 'Running',
        'pytorch-operator': 'Running',
        'seldon-controller-manager': 'Running',
        'tfjob-operator': 'Running',
    }


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
            'pytorchjobs.kubeflow.org',
            'scheduledworkflows.kubeflow.org',
            'seldondeployments.machinelearning.seldon.io',
            'servicerolebindings.rbac.istio.io',
            'serviceroles.rbac.istio.io',
            'suggestions.kubeflow.org',
            'tfjobs.kubeflow.org',
            'trials.kubeflow.org',
            'viewers.kubeflow.org',
            'workflows.argoproj.io',
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
            'pytorchjobs.kubeflow.org',
            'scheduledworkflows.kubeflow.org',
            'seldondeployments.machinelearning.seldon.io',
            'servicerolebindings.rbac.istio.io',
            'serviceroles.rbac.istio.io',
            'tfjobs.kubeflow.org',
            'viewers.kubeflow.org',
            'workflows.argoproj.io',
        }
    )


@pytest.mark.edge
def test_crd_created_edge():
    crds = yaml.safe_load(kubectl.get('crd', '-oyaml').stdout)

    names = {i['metadata']['name'] for i in crds['items']}
    assert names.issuperset(
        {
            'pytorchjobs.kubeflow.org',
            'scheduledworkflows.kubeflow.org',
            'seldondeployments.machinelearning.seldon.io',
            'tfjobs.kubeflow.org',
            'workflows.argoproj.io',
        }
    )


@pytest.mark.full
def test_service_accounts_created_full():
    sas = yaml.safe_load(kubectl.get('sa', '-oyaml').stdout)

    names = {i['metadata']['name'] for i in sas['items']}
    assert names.issuperset(
        {
            'admission-webhook',
            'admission-webhook-operator',
            'argo-controller',
            'argo-controller-operator',
            'default',
            'dex-auth',
            'dex-auth-operator',
            'istio-ingressgateway',
            'istio-ingressgateway-operator',
            'istio-pilot',
            'istio-pilot-operator',
            'jupyter-controller',
            'jupyter-controller-operator',
            'jupyter-ui',
            'jupyter-ui-operator',
            'katib-controller',
            'katib-controller-operator',
            'katib-db-manager',
            'katib-db-manager-operator',
            'katib-db-operator',
            'katib-ui',
            'katib-ui-operator',
            'kfp-api',
            'kfp-api-operator',
            'kfp-db-operator',
            'kfp-persistence',
            'kfp-persistence-operator',
            'kfp-schedwf',
            'kfp-schedwf-operator',
            'kfp-ui',
            'kfp-ui-operator',
            'kfp-viewer',
            'kfp-viewer-operator',
            'kfp-viz-operator',
            'kubeflow-dashboard',
            'kubeflow-dashboard-operator',
            'kubeflow-profiles',
            'kubeflow-profiles-operator',
            'kubeflow-volumes',
            'kubeflow-volumes-operator',
            'minio-operator',
            'mlmd-operator',
            'oidc-gatekeeper-operator',
            'pipeline-runner',
            'pytorch-operator',
            'pytorch-operator-operator',
            'seldon-controller-manager',
            'seldon-controller-manager-operator',
            'spark',
            'spark-operator',
            'tfjob-operator',
            'tfjob-operator-operator',
        },
    )


@pytest.mark.lite
def test_service_accounts_created_lite():
    sas = yaml.safe_load(kubectl.get('sa', '-oyaml').stdout)

    names = {i['metadata']['name'] for i in sas['items']}
    assert names.issuperset(
        {
            'admission-webhook',
            'admission-webhook-operator',
            'argo-controller',
            'argo-controller-operator',
            'default',
            'dex-auth',
            'dex-auth-operator',
            'istio-ingressgateway',
            'istio-ingressgateway-operator',
            'istio-pilot',
            'istio-pilot-operator',
            'jupyter-controller',
            'jupyter-controller-operator',
            'jupyter-ui',
            'jupyter-ui-operator',
            'kfp-api',
            'kfp-api-operator',
            'kfp-db-operator',
            'kfp-persistence',
            'kfp-persistence-operator',
            'kfp-schedwf',
            'kfp-schedwf-operator',
            'kfp-ui',
            'kfp-ui-operator',
            'kfp-viewer',
            'kfp-viewer-operator',
            'kfp-viz-operator',
            'kubeflow-dashboard',
            'kubeflow-dashboard-operator',
            'kubeflow-profiles',
            'kubeflow-profiles-operator',
            'kubeflow-volumes',
            'kubeflow-volumes-operator',
            'minio-operator',
            'mlmd-operator',
            'oidc-gatekeeper-operator',
            'pipeline-runner',
            'pytorch-operator',
            'pytorch-operator-operator',
            'seldon-controller-manager',
            'seldon-controller-manager-operator',
            'tfjob-operator',
            'tfjob-operator-operator',
        },
    )


@pytest.mark.edge
def test_service_accounts_created_edge():
    sas = yaml.safe_load(kubectl.get('sa', '-oyaml').stdout)

    names = {i['metadata']['name'] for i in sas['items']}
    assert names.issuperset(
        {
            'argo-controller',
            'argo-controller-operator',
            'default',
            'kfp-api',
            'kfp-api-operator',
            'kfp-db-operator',
            'kfp-persistence',
            'kfp-persistence-operator',
            'kfp-schedwf',
            'kfp-schedwf-operator',
            'minio-operator',
            'pipeline-runner',
            'pytorch-operator',
            'pytorch-operator-operator',
            'seldon-controller-manager',
            'seldon-controller-manager-operator',
            'tfjob-operator',
            'tfjob-operator-operator',
        },
    )
