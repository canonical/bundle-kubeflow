"""Runs tests by inspecting microk8s with kubectl."""

import yaml
from sh import Command

kubectl = Command('juju-kubectl')


def test_running():
    pods = yaml.safe_load(kubectl.get('pods', '-oyaml').stdout)

    statuses = sorted(
        (i['metadata']['labels']['juju-app'], i['status']['phase'])
        for i in pods['items']
        if 'juju-app' in i['metadata']['labels']
    )

    assert statuses == [
        ('ambassador', 'Running'),
        ('argo-controller', 'Running'),
        ('argo-ui', 'Running'),
        ('dex-auth', 'Running'),
        ('jupyter-controller', 'Running'),
        ('jupyter-web', 'Running'),
        ('katib-controller', 'Running'),
        ('katib-db', 'Running'),
        ('katib-manager', 'Running'),
        ('katib-ui', 'Running'),
        ('kubeflow-dashboard', 'Running'),
        ('kubeflow-profiles', 'Running'),
        ('metacontroller', 'Running'),
        ('metadata-api', 'Running'),
        ('metadata-db', 'Running'),
        ('metadata-envoy', 'Running'),
        ('metadata-grpc', 'Running'),
        ('metadata-ui', 'Running'),
        ('minio', 'Running'),
        ('modeldb-backend', 'Running'),
        ('modeldb-db', 'Running'),
        ('modeldb-store', 'Running'),
        ('modeldb-ui', 'Running'),
        ('oidc-gatekeeper', 'Running'),
        ('pipelines-api', 'Running'),
        ('pipelines-db', 'Running'),
        ('pipelines-persistence', 'Running'),
        ('pipelines-scheduledworkflow', 'Running'),
        ('pipelines-ui', 'Running'),
        ('pipelines-viewer', 'Running'),
        ('pipelines-visualization', 'Running'),
        ('pytorch-operator', 'Running'),
        ('seldon-core', 'Running'),
        ('tf-job-operator', 'Running'),
    ]


def test_crd_created():
    crds = yaml.safe_load(kubectl.get('crd', '-oyaml').stdout)

    names = sorted(i['metadata']['name'] for i in crds['items'])
    assert names == [
        'authcodes.dex.coreos.com',
        'authrequests.dex.coreos.com',
        'compositecontrollers.metacontroller.k8s.io',
        'connectors.dex.coreos.com',
        'controllerrevisions.metacontroller.k8s.io',
        'decoratorcontrollers.metacontroller.k8s.io',
        'experiments.kubeflow.org',
        'notebooks.kubeflow.org',
        'oauth2clients.dex.coreos.com',
        'offlinesessionses.dex.coreos.com',
        'passwords.dex.coreos.com',
        'poddefaults.kubeflow.org',
        'profiles.kubeflow.org',
        'pytorchjobs.kubeflow.org',
        'refreshtokens.dex.coreos.com',
        'scheduledworkflows.kubeflow.org',
        'seldondeployments.machinelearning.seldon.io',
        'servicerolebindings.rbac.istio.io',
        'serviceroles.rbac.istio.io',
        'signingkeies.dex.coreos.com',
        'suggestions.kubeflow.org',
        'tfjobs.kubeflow.org',
        'trials.kubeflow.org',
        'viewers.kubeflow.org',
        'workflows.argoproj.io',
    ]


def test_service_accounts_created():
    crds = yaml.safe_load(kubectl.get('sa', '-oyaml').stdout)

    names = sorted(i['metadata']['name'] for i in crds['items'])
    assert names == [
        'ambassador',
        'ambassador-operator',
        'argo-controller',
        'argo-controller-operator',
        'argo-ui',
        'argo-ui-operator',
        'default',
        'dex-auth',
        'dex-auth-operator',
        'jupyter-controller',
        'jupyter-controller-operator',
        'jupyter-notebook',
        'jupyter-web',
        'jupyter-web-operator',
        'katib-controller',
        'katib-controller-operator',
        'katib-db-operator',
        'katib-manager-operator',
        'katib-ui',
        'katib-ui-operator',
        'kubeflow-dashboard',
        'kubeflow-dashboard-operator',
        'kubeflow-profiles',
        'kubeflow-profiles-operator',
        'metacontroller',
        'metacontroller-operator',
        'metadata-api-operator',
        'metadata-db-operator',
        'metadata-envoy-operator',
        'metadata-grpc-operator',
        'metadata-ui',
        'metadata-ui-operator',
        'minio-operator',
        'modeldb-backend-operator',
        'modeldb-db-operator',
        'modeldb-store-operator',
        'modeldb-ui-operator',
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
        'seldon-core',
        'seldon-core-operator',
        'tf-job-operator',
        'tf-job-operator-operator',
    ]


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
