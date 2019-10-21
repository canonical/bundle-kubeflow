import os
from pathlib import Path

import yaml
from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import set_flag, clear_flag, when, when_any, when_not


@when('charm.started')
def charm_ready():
    layer.status.active('')


@when_any('layer.docker-resource.oci-image.changed', 'config.changed')
def update_image():
    clear_flag('charm.started')


@when('layer.docker-resource.oci-image.available')
@when_not('charm.started')
def start_charm():
    layer.status.maintenance('configuring container')

    config = hookenv.config()
    image_info = layer.docker_resource.get_info('oci-image')

    crd = yaml.load(Path('files/crd-v1beta1.yaml').read_text())

    conf_data = {}
    if config['pytorch-default-image']:
        conf_data['pytorchImage'] = config['pytorch-default-image']

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
            'serviceAccount': {
                'rules': [
                    {
                        'apiGroups': ['kubeflow.org'],
                        'resources': ['pytorchjobs', 'pytorchjobs/status'],
                        'verbs': ['*'],
                    },
                    {
                        'apiGroups': ['apiextensions.k8s.io'],
                        'resources': ['customresourcedefinitions'],
                        'verbs': ['*'],
                    },
                    {
                        'apiGroups': ['storage.k8s.io'],
                        'resources': ['storageclasses'],
                        'verbs': ['*'],
                    },
                    {'apiGroups': ['batch'], 'resources': ['jobs'], 'verbs': ['*']},
                    {
                        'apiGroups': [''],
                        'resources': [
                            'configmaps',
                            'pods',
                            'services',
                            'endpoints',
                            'persistentvolumeclaims',
                            'events',
                        ],
                        'verbs': ['*'],
                    },
                    {
                        'apiGroups': ['apps', 'extensions'],
                        'resources': ['deployments'],
                        'verbs': ['*'],
                    },
                ]
            },
            'containers': [
                {
                    'name': 'pytorch-operator',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'command': [
                        '/pytorch-operator.v1',
                        '--alsologtostderr',
                        '-v=1',
                        '--monitoring-port=8443',
                    ],
                    'config': {'KUBEFLOW_NAMESPACE': os.environ['JUJU_MODEL_NAME']},
                    'files': [
                        {
                            'name': 'configs',
                            'mountPath': '/etc/config',
                            'files': {'controller_config_file.yaml': yaml.dump(conf_data)},
                        }
                    ],
                }
            ],
        },
        {
            'kubernetesResources': {
                'customResourceDefinitions': {crd['metadata']['name']: crd['spec']}
            }
        },
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
