from glob import glob
from pathlib import Path

import yaml
from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import (
    clear_flag,
    is_flag_set,
    register_trigger,
    set_flag,
    when,
    when_any,
    when_not,
)

register_trigger(when='endpoint.ambassador.joined', clear_flag='charm.started')
register_trigger(when_not='endpoint.ambassador.joined', clear_flag='charm.started')


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
    service_name = hookenv.service_name()

    hub_port = 8000
    api_port = 8081

    if is_flag_set('endpoint.ambassador.joined'):
        annotations = {
            'getambassador.io/config': yaml.dump_all(
                [
                    {
                        'apiVersion': 'ambassador/v0',
                        'kind': 'Mapping',
                        'name': 'tf_hub',
                        'prefix': '/hub',
                        'rewrite': '/hub',
                        'service': f'{service_name}:{hub_port}',
                        'use_websocket': True,
                        'timeout_ms': 30000,
                    },
                    {
                        'apiVersion': 'ambassador/v0',
                        'kind': 'Mapping',
                        'name': 'tf_hub_user',
                        'prefix': '/user',
                        'rewrite': '/user',
                        'service': f'{service_name}:{hub_port}',
                        'use_websocket': True,
                        'timeout_ms': 30000,
                    },
                ]
            )
        }
    else:
        annotations = {}

    pip_installs = [
        'kubernetes==9.0.0',
        'jhub-remote-user-authenticator',
        'jupyterhub-dummyauthenticator',
        'jupyterhub-kubespawner',
        'oauthenticator',
    ]

    layer.caas_base.pod_spec_set(
        {
            'service': {'annotations': annotations},
            'containers': [
                {
                    'name': 'jupyterhub',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'command': [
                        'bash',
                        '-c',
                        f'pip install {" ".join(pip_installs)} && jupyterhub -f /etc/config/jupyterhub_config.py',
                    ],
                    'ports': [
                        {'name': 'hub', 'containerPort': hub_port},
                        {'name': 'api', 'containerPort': api_port},
                    ],
                    'config': {
                        'K8S_SERVICE_NAME': service_name,
                        'AUTHENTICATOR': config['authenticator'],
                        'NOTEBOOK_STORAGE_SIZE': config['notebook-storage-size'],
                        'NOTEBOOK_STORAGE_CLASS': config['notebook-storage-class'],
                        'NOTEBOOK_IMAGE': config['notebook-image'],
                    },
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
