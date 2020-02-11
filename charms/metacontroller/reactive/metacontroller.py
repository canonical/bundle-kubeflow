from pathlib import Path

import yaml
from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import hook, set_flag, clear_flag, when, when_any, when_not


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

    debug_port = hookenv.config('debug-port')

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
            'serviceAccount': {
                'global': True,
                'rules': [
                    {'apiGroups': ['*'], 'resources': ['*'], 'verbs': ['*']},
                    {'nonResourceURLs': ['*'], 'verbs': ['*']},
                ],
            },
            'containers': [
                {
                    'name': 'metacontroller',
                    'command': [
                        '/usr/bin/metacontroller',
                        '--logtostderr',
                        '-v=4',
                        '--discovery-interval=20s',
                        f'--debug-addr={debug_port}',
                    ],
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'ports': [{'name': 'debug-http', 'containerPort': debug_port}],
                }
            ],
        },
        {
            'kubernetesResources': {
                'customResourceDefinitions': {
                    crd['metadata']['name']: crd['spec']
                    for crd in yaml.safe_load_all(Path("files/crds.yaml").read_text())
                }
            }
        },
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
