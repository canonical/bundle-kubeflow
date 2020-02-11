import os
from pathlib import Path

import yaml

from charms import layer
from charms.reactive import clear_flag, hook, hookenv, set_flag, when, when_any, when_not


@hook('upgrade-charm')
def upgrade_charm():
    clear_flag('charm.started')


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

    image_info = layer.docker_resource.get_info('oci-image')
    service_name = hookenv.service_name()

    crd = yaml.load(Path('files/crd-v1beta1.yaml').read_text())

    port = hookenv.config('port')

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
            'serviceAccount': {
                'global': True,
                'rules': [
                    {
                        'apiGroups': ['*'],
                        'resources': ['deployments', 'services'],
                        'verbs': ['create', 'get', 'list', 'watch', 'update', 'patch', 'delete'],
                    },
                    {
                        'apiGroups': ['kubeflow.org'],
                        'resources': ['viewers'],
                        'verbs': ['create', 'get', 'list', 'watch', 'update', 'patch', 'delete'],
                    },
                ],
            },
            'service': {
                'annotations': {
                    'getambassador.io/config': yaml.dump_all(
                        [
                            {
                                'apiVersion': 'ambassador/v0',
                                'kind': 'Mapping',
                                'name': 'pipelines-viewer',
                                'prefix': '/data',
                                'rewrite': '/data',
                                'service': f'{service_name}:{port}',
                                'use_websocket': True,
                                'timeout_ms': 30000,
                            }
                        ]
                    )
                }
            },
            'containers': [
                {
                    'name': 'pipelines-viewer',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'config': {'POD_NAMESPACE': os.environ['JUJU_MODEL_NAME']},
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
