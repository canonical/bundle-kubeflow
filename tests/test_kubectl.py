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
        ('jupyterhub', 'Running'),
        ('katib-controller', 'Running'),
        ('katib-db', 'Running'),
        ('katib-manager', 'Running'),
        ('katib-ui', 'Running'),
        ('mariadb', 'Running'),
        ('metacontroller', 'Running'),
        ('minio', 'Running'),
        ('modeldb-backend', 'Running'),
        ('modeldb-store', 'Running'),
        ('modeldb-ui', 'Running'),
        ('pipelines-api', 'Running'),
        ('pipelines-dashboard', 'Running'),
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
        'tfjobs.kubeflow.org',
        'trials.kubeflow.org',
        'viewers.kubeflow.org',
        'workflows.argoproj.io',
    ]


def test_service_accounts_created():
    crds = yaml.safe_load(kubectl.get('sa', '-oyaml').stdout)

    names = sorted(i['metadata']['name'] for i in crds['items'])
    assert names == [
        'argo',
        'argo-ui',
        'default',
        'jupyter',
        'jupyter-notebook',
        'meta-controller-service',
        'ml-pipeline-scheduledworkflow',
        'pipeline-runner',
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
