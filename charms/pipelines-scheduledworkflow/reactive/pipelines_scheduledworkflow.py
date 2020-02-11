import os
from pathlib import Path

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


@when('layer.docker-resource.oci-image.available')
@when_not('charm.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    crd = yaml.load(Path('files/crd-v1beta1.yaml').read_text())

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
            'serviceAccount': {
                'global': True,
                'rules': [
                    #  {'apiGroups': ['*'], 'resources': ['*'], 'verbs': ['*']},
                    #  {'nonResourceURLs': ['*'], 'verbs': ['*']},
                    {
                        'apiGroups': ['argoproj.io'],
                        'resources': ['workflows'],
                        'verbs': ['create', 'get', 'list', 'watch', 'update', 'patch', 'delete'],
                    },
                    {
                        'apiGroups': ['kubeflow.org'],
                        'resources': ['scheduledworkflows'],
                        'verbs': [
                            'get',
                            'list',
                            'watch',
                            'create',
                            'delete',
                            'deletecollection',
                            'patch',
                            'update',
                        ],
                    },
                ],
            },
            'containers': [
                {
                    'name': 'pipelines-scheduledworkflow',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'config': {'POD_NAMESPACE': os.environ['JUJU_MODEL_NAME']},
                }
            ],
        },
        k8s_resources={
            'kubernetesResources': {
                'customResourceDefinitions': {crd['metadata']['name']: crd['spec']}
            }
        },
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
