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
        ('ambassador-auth', 'Running'),
        ('argo-controller', 'Running'),
        ('argo-ui', 'Running'),
        ('jupyter-controller', 'Running'),
        ('jupyter-web', 'Running'),
        ('katib-controller', 'Running'),
        ('katib-db', 'Running'),
        ('katib-manager', 'Running'),
        ('katib-ui', 'Running'),
        ('metacontroller', 'Running'),
        ('minio', 'Running'),
        ('modeldb-backend', 'Running'),
        ('modeldb-db', 'Running'),
        ('modeldb-store', 'Running'),
        ('modeldb-ui', 'Running'),
        ('pipelines-api', 'Running'),
        ('pipelines-dashboard', 'Running'),
        ('pipelines-db', 'Running'),
        ('pipelines-persistence', 'Running'),
        ('pipelines-scheduledworkflow', 'Running'),
        ('pipelines-ui', 'Running'),
        ('pipelines-viewer', 'Running'),
        ('pytorch-operator', 'Running'),
        ('redis', 'Running'),
        ('seldon-api-frontend', 'Running'),
        ('seldon-cluster-manager', 'Running'),
        ('tensorboard', 'Running'),
        ('tf-job-dashboard', 'Running'),
        ('tf-job-operator', 'Running'),
    ]


def test_crd_created():
    crds = yaml.safe_load(kubectl.get('crd', '-oyaml').stdout)

    names = sorted(i['metadata']['name'] for i in crds['items'])
    assert names == [
        'compositecontrollers.metacontroller.k8s.io',
        'controllerrevisions.metacontroller.k8s.io',
        'decoratorcontrollers.metacontroller.k8s.io',
        'experiments.kubeflow.org',
        'notebooks.kubeflow.org',
        'pytorchjobs.kubeflow.org',
        'scheduledworkflows.kubeflow.org',
        'seldondeployments.machinelearning.seldon.io',
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
        'ambassador-auth-operator',
        'ambassador-operator',
        'argo-controller',
        'argo-controller-operator',
        'argo-ui',
        'argo-ui-operator',
        'default',
        'jupyter-controller',
        'jupyter-controller-operator',
        'jupyter-web-operator',
        'katib-controller',
        'katib-controller-operator',
        'katib-db-operator',
        'katib-manager-operator',
        'katib-ui',
        'katib-ui-operator',
        'metacontroller',
        'metacontroller-operator',
        'minio-operator',
        'modeldb-backend-operator',
        'modeldb-db-operator',
        'modeldb-store-operator',
        'modeldb-ui-operator',
        'pipeline-runner',
        'pipelines-api',
        'pipelines-api-operator',
        'pipelines-dashboard-operator',
        'pipelines-db-operator',
        'pipelines-persistence-operator',
        'pipelines-scheduledworkflow',
        'pipelines-scheduledworkflow-operator',
        'pipelines-ui-operator',
        'pipelines-viewer-operator',
        'pytorch-operator',
        'pytorch-operator-operator',
        'redis-operator',
        'seldon-api-frontend-operator',
        'seldon-cluster-manager-operator',
        'tensorboard-operator',
        'tf-job-dashboard',
        'tf-job-dashboard-operator',
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
