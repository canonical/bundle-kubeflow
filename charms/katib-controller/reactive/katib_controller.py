import json
import os
from glob import glob
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
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/file-metrics-collector"
            },
            "File": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/file-metrics-collector"
            },
            "TensorFlowEvent": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/tfevent-metrics-collector"
            },
        }
    ),
    'suggestion': json.dumps(
        {
            "random": {"image": "gcr.io/kubeflow-images-public/katib/v1alpha3/suggestion-hyperopt"},
            "grid": {"image": "gcr.io/kubeflow-images-public/katib/v1alpha3/suggestion-chocolate"},
            "hyperband": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/suggestion-hyperband"
            },
            "bayesianoptimization": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/suggestion-skopt"
            },
            "tpe": {"image": "gcr.io/kubeflow-images-public/katib/v1alpha3/suggestion-hyperopt"},
            "nasrl": {"image": "gcr.io/kubeflow-images-public/katib/v1alpha3/suggestion-nasrl"},
        }
    ),
}

TRIAL_TEMPLATE = {
    'defaultTrialTemplate.yaml': json.dumps(
        {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {"name": "{{.Trial}}", "namespace": "{{.NameSpace}}"},
            "spec": {
                "template": {
                    "spec": {
                        "containers": [{"name": "{{.Trial}}", "image": "alpine"}],
                        "restartPolicy": "Never",
                    }
                }
            },
        }
    )
}


@when('layer.docker-resource.oci-image.available')
@when_not('charm.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    crds = [yaml.load(Path(crd).read_text()) for crd in glob('files/*-crd.yaml')]

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
                            'trials',
                            'trials/status',
                            'suggestions',
                            'suggestions/status',
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
                'customResourceDefinitions': {crd['metadata']['name']: crd['spec'] for crd in crds}
            },
            'configMaps': {'katib-config': KATIB_CONFIG, 'trial-template': TRIAL_TEMPLATE},
        },
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
