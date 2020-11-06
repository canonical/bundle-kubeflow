import json
import os
from pathlib import Path

import yaml

from charmhelpers.core import hookenv
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
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/file-metrics-collector:v0.9.0"
            },
            "File": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/file-metrics-collector:v0.9.0"
            },
            "TensorFlowEvent": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/tfevent-metrics-collector:v0.9.0"
            },
        }
    ),
    'suggestion': json.dumps(
        {
            "random": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/suggestion-hyperopt:v0.9.0"
            },
            "grid": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/suggestion-chocolate:v0.9.0"
            },
            "hyperband": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/suggestion-hyperband:v0.9.0"
            },
            "bayesianoptimization": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/suggestion-skopt:v0.9.0"
            },
            "tpe": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/suggestion-hyperopt:v0.9.0"
            },
            "nasrl": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/suggestion-nasrl:v0.9.0"
            },
        }
    ),
}


@when('layer.docker-resource.oci-image.available')
@when_not('charm.started')
def start_charm():
    if not hookenv.is_leader():
        hookenv.log("This unit is not a leader.")
        return False

    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')
    config = dict(hookenv.config())

    layer.caas_base.pod_spec_set(
        {
            'version': 3,
            'serviceAccount': {
                'roles': [
                    {
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
                            {
                                'apiGroups': ['batch'],
                                'resources': ['jobs', 'cronjobs'],
                                'verbs': ['*'],
                            },
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
                    }
                ]
            },
            'containers': [
                {
                    'name': 'katib-controller',
                    'command': ["./katib-controller"],
                    'args': [
                        '-webhook-port',
                        str(config['webhook-port']),
                        '-logtostderr',
                        '-v=4',
                        '-cert-localfs=true',
                    ],
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'ports': [
                        {'name': 'webhook', 'containerPort': config['webhook-port']},
                        {'name': 'metrics', 'containerPort': config['metrics-port']},
                    ],
                    'envConfig': {'KATIB_CORE_NAMESPACE': os.environ['JUJU_MODEL_NAME']},
                    'kubernetes': {'securityContext': {'runAsUser': 0}},
                }
            ],
        },
        k8s_resources={
            'kubernetesResources': {
                'customResourceDefinitions': [
                    {'name': crd['metadata']['name'], 'spec': crd['spec']}
                    for crd in yaml.safe_load_all(Path("files/crds.yaml").read_text())
                ],
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
