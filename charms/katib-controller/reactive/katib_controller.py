import json
import os
from pathlib import Path
from subprocess import run

import yaml

from charms import layer
from charms.reactive import clear_flag, hook, set_flag, when, when_not


@hook('upgrade-charm')
def upgrade_charm():
    clear_flag('charm.started')


@when('charm.started')
def charm_ready():
    layer.status.active('')


@when('layer.docker-resource.oci-image.changed')
def update_image():
    clear_flag('charm.started')


KATIB_CONFIG = {
    'metrics-collector-sidecar': json.dumps(
        {
            "StdOut": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/file-metrics-collector:v0.8.0"
            },
            "File": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/file-metrics-collector:v0.8.0"
            },
            "TensorFlowEvent": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/tfevent-metrics-collector:v0.8.0"
            },
        }
    ),
    'suggestion': json.dumps(
        {
            "random": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/suggestion-hyperopt:v0.8.0"
            },
            "grid": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/suggestion-chocolate:v0.8.0"
            },
            "hyperband": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/suggestion-hyperband:v0.8.0"
            },
            "bayesianoptimization": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/suggestion-skopt:v0.8.0"
            },
            "tpe": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/suggestion-hyperopt:v0.8.0"
            },
            "nasrl": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/suggestion-nasrl:v0.8.0"
            },
        }
    ),
}


@when('layer.docker-resource.oci-image.available')
@when_not('charm.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:4096",
            "-keyout",
            "key.pem",
            "-out",
            "cert.pem",
            "-days",
            "365",
            "-subj",
            "/CN=localhost",
            "-nodes",
        ],
        check=True,
    )

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
            'serviceAccount': {
                'rules': [
                    {
                        'apiGroups': [''],
                        'resources': [
                            'configmaps',
                            'serviceaccounts',
                            'services',
                            'secrets',
                            'events',
                            'namespaces',
                        ],
                        'verbs': ['*'],
                    },
                    {
                        'apiGroups': [''],
                        'resources': ['pods', 'pods/log', 'pods/status'],
                        'verbs': ['*'],
                    },
                    {'apiGroups': ['apps'], 'resources': ['deployments'], 'verbs': ['*']},
                    {'apiGroups': ['batch'], 'resources': ['jobs', 'cronjobs'], 'verbs': ['*']},
                    {
                        'apiGroups': ['apiextensions.k8s.io'],
                        'resources': ['customresourcedefinitions'],
                        'verbs': ['create', 'get'],
                    },
                    {
                        'apiGroups': ['admissionregistration.k8s.io'],
                        'resources': [
                            'validatingwebhookconfigurations',
                            'mutatingwebhookconfigurations',
                        ],
                        'verbs': ['*'],
                    },
                    {
                        'apiGroups': ['kubeflow.org'],
                        'resources': [
                            'experiments',
                            'experiments/status',
                            'experiments/finalizers',
                            'trials',
                            'trials/status',
                            'trials/finalizers',
                            'suggestions',
                            'suggestions/status',
                            'suggestions/finalizers',
                        ],
                        'verbs': ['*'],
                    },
                    {
                        'apiGroups': ['kubeflow.org'],
                        'resources': ['tfjobs', 'pytorchjobs'],
                        'verbs': ['*'],
                    },
                ]
            },
            'containers': [
                {
                    'name': 'katib-controller',
                    'command': ["./katib-controller"],
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'ports': [{'name': 'webhook', 'containerPort': 443}],
                    'config': {'KATIB_CORE_NAMESPACE': os.environ['JUJU_MODEL_NAME']},
                    'files': [
                        {
                            'name': 'cert',
                            'mountPath': '/tmp/cert',
                            'files': {
                                'cert.pem': Path('cert.pem').read_text(),
                                'key.pem': Path('key.pem').read_text(),
                            },
                        }
                    ],
                }
            ],
        },
        k8s_resources={
            'kubernetesResources': {
                'customResourceDefinitions': {
                    crd['metadata']['name']: crd['spec']
                    for crd in yaml.safe_load_all(Path("files/crds.yaml").read_text())
                }
            },
            'configMaps': {
                'katib-config': KATIB_CONFIG,
                'trial-template': {
                    'defaultTrialTemplate.yaml': Path(
                        'files/defaultTrialTemplate.yaml.tmpl'
                    ).read_text()
                },
            },
        },
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
