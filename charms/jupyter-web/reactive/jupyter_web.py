from glob import glob
from pathlib import Path

import yaml
from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import clear_flag, set_flag, when, when_any, when_not


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
            'service': {
                'annotations': {
                    'getambassador.io/config': yaml.dump_all(
                        [
                            {
                                'apiVersion': 'ambassador/v0',
                                'kind': 'Mapping',
                                'name': 'jupyter-web',
                                'prefix': '/jupyter/',
                                'service': f'{service_name}:{port}',
                                'timeout_ms': 30000,
                                'add_request_headers': {'x-forwarded-prefix': '/jupyter'},
                            }
                        ]
                    )
                }
            },
            'containers': [
                {
                    'name': 'jupyterhub',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'ports': [{'name': 'http', 'containerPort': port}],
                    'files': [
                        {
                            'name': 'configs',
                            'mountPath': '/etc/config',
                            'files': {
                                Path(filename).name: Path(filename).read_text()
                                for filename in glob('files/*')
                            },
                        }
                    ],
                }
            ],
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
