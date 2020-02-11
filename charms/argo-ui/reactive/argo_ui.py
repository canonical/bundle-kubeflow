import os

import yaml
from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import hook, clear_flag, set_flag, when, when_any, when_not


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

    port = hookenv.config('port')

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
            'serviceAccount': {
                'global': True,
                'rules': [
                    {
                        'apiGroups': [''],
                        'resources': ['pods', 'pods/exec', 'pods/log'],
                        'verbs': ['get', 'list', 'watch'],
                    },
                    {'apiGroups': [''], 'resources': ['secrets'], 'verbs': ['get']},
                    {
                        'apiGroups': ['argoproj.io'],
                        'resources': ['workflows', 'workflows/finalizers'],
                        'verbs': ['get', 'list', 'watch'],
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
                                'name': 'argo-ui',
                                'prefix': '/argo/',
                                'service': f'{service_name}:{port}',
                                'timeout_ms': 30000,
                            }
                        ]
                    )
                }
            },
            'containers': [
                {
                    'name': 'argo-ui',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'config': {
                        'ARGO_NAMESPACE': os.environ['JUJU_MODEL_NAME'],
                        'IN_CLUSTER': 'true',
                        'BASE_HREF': '/argo/',
                    },
                    'ports': [{'name': 'http-ui', 'containerPort': port}],
                    'kubernetes': {'readinessProbe': {'httpGet': {'path': '/', 'port': port}}},
                }
            ],
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
