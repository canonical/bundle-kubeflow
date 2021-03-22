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
        'argo-ui': 'Running',
        'dex-auth': 'Running',
        'istio-ingressgateway': 'Running',
        'istio-pilot': 'Running',
        'jupyter-controller': 'Running',
        'jupyter-ui': 'Running',
        'katib-controller': 'Running',
        'katib-db': 'Running',
        'katib-db-manager': 'Running',
        'katib-ui': 'Running',
        'kubeflow-dashboard': 'Running',
        'kubeflow-profiles': 'Running',
        'metadata-api': 'Running',
        'metadata-db': 'Running',
        'metadata-envoy': 'Running',
        'metadata-grpc': 'Running',
        'metadata-ui': 'Running',
        'minio': 'Running',
        'oidc-gatekeeper': 'Running',
        'pipelines-api': 'Running',
        'pipelines-db': 'Running',
        'pipelines-persistence': 'Running',
        'pipelines-scheduledworkflow': 'Running',
        'pipelines-ui': 'Running',
        'pipelines-viewer': 'Running',
        'pipelines-visualization': 'Running',
        'pytorch-operator': 'Running',
        'seldon-controller-manager': 'Running',
        'tf-job-operator': 'Running',
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
        'minio': 'Running',
        'oidc-gatekeeper': 'Running',
        'pipelines-api': 'Running',
        'pipelines-db': 'Running',
        'pipelines-persistence': 'Running',
        'pipelines-scheduledworkflow': 'Running',
        'pipelines-ui': 'Running',
        'pipelines-viewer': 'Running',
        'pipelines-visualization': 'Running',
        'pytorch-operator': 'Running',
        'seldon-controller-manager': 'Running',
        'tf-job-operator': 'Running',
    }


@pytest.mark.edge
@flaky(max_runs=60, rerun_filter=lambda *_: sleep(5) or True)
def test_running_edge():
    assert get_statuses() == {
        'argo-controller': 'Running',
        'minio': 'Running',
        'pipelines-api': 'Running',
        'pipelines-db': 'Running',
        'pipelines-persistence': 'Running',
        'pipelines-scheduledworkflow': 'Running',
        'pytorch-operator': 'Running',
        'seldon-controller-manager': 'Running',
        'tf-job-operator': 'Running',
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
            'argo-ui',
            'argo-ui-operator',
            'default',
            'dex-auth',
            'dex-auth-operator',
            'istio-ingressgateway',
            'istio-ingressgateway-operator',
            'istio-pilot',
            'istio-pilot-operator',
            'jupyter-controller',
            'jupyter-controller-operator',
            'jupyter-notebook',
            'jupyter-ui',
            'jupyter-ui-operator',
            'katib-controller',
            'katib-controller-operator',
            'katib-db-operator',
            'katib-db-manager-operator',
            'katib-ui',
            'katib-ui-operator',
            'kubeflow-dashboard',
            'kubeflow-dashboard-operator',
            'kubeflow-profiles',
            'kubeflow-profiles-operator',
            'metadata-api-operator',
            'metadata-db-operator',
            'metadata-envoy-operator',
            'metadata-grpc-operator',
            'metadata-ui',
            'metadata-ui-operator',
            'minio-operator',
            'oidc-gatekeeper-operator',
            'pipeline-runner',
            'pipelines-api',
            'pipelines-api-operator',
            'pipelines-db-operator',
            'pipelines-persistence',
            'pipelines-persistence-operator',
            'pipelines-scheduledworkflow',
            'pipelines-scheduledworkflow-operator',
            'pipelines-ui',
            'pipelines-ui-operator',
            'pipelines-viewer',
            'pipelines-viewer-operator',
            'pipelines-visualization-operator',
            'pytorch-operator',
            'pytorch-operator-operator',
            'seldon-controller-manager',
            'seldon-controller-manager-operator',
            'tf-job-operator',
            'tf-job-operator-operator',
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
            'jupyter-notebook',
            'jupyter-ui',
            'jupyter-ui-operator',
            'kubeflow-dashboard',
            'kubeflow-dashboard-operator',
            'kubeflow-profiles',
            'kubeflow-profiles-operator',
            'minio-operator',
            'oidc-gatekeeper-operator',
            'pipeline-runner',
            'pipelines-api',
            'pipelines-api-operator',
            'pipelines-db-operator',
            'pipelines-persistence',
            'pipelines-persistence-operator',
            'pipelines-scheduledworkflow',
            'pipelines-scheduledworkflow-operator',
            'pipelines-ui',
            'pipelines-ui-operator',
            'pipelines-viewer',
            'pipelines-viewer-operator',
            'pipelines-visualization-operator',
            'pytorch-operator',
            'pytorch-operator-operator',
            'seldon-controller-manager',
            'seldon-controller-manager-operator',
            'tf-job-operator',
            'tf-job-operator-operator',
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
            'minio-operator',
            'pipeline-runner',
            'pipelines-api',
            'pipelines-api-operator',
            'pipelines-db-operator',
            'pipelines-persistence',
            'pipelines-persistence-operator',
            'pipelines-scheduledworkflow',
            'pipelines-scheduledworkflow-operator',
            'pytorch-operator',
            'pytorch-operator-operator',
            'seldon-controller-manager',
            'seldon-controller-manager-operator',
            'tf-job-operator',
            'tf-job-operator-operator',
        },
    )


# TODO: Failing in Travis
# def test_tfjob_create():
#     response = kubectl.create('-f', 'charms/tf-job-operator/files/mnist.yaml')
#     assert response.strip() == 'tfjob.kubeflow.org/kubeflow-mnist-test created'
#
#     for i in range(60):
#         tfjobs = yaml.safe_load(kubectl.get('tfjobs', '-oyaml').stdout)['items']
#
#         try:
#             statuses = [
#                 (
#                     j['metadata']['name'],
#                     [(c['reason'], c['status']) for c in j['status']['conditions']],
#                 )
#                 for j in tfjobs
#             ]
#             assert statuses == [
#                 (
#                     'kubeflow-mnist-test',
#                     [
#                         ('TFJobCreated', 'True'),
#                         ('TFJobRunning', 'False'),
#                         ('TFJobSucceeded', 'True'),
#                     ],
#                 )
#             ]
#
#             break
#         except (AssertionError, KeyError) as err:
#             print("Waiting for TFJob to complete...")
#             print(err)
#             time.sleep(5)
#     else:
#         pytest.fail("Waited too long for TFJob to succeed!")
