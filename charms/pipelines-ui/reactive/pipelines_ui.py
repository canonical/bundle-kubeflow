import os

import yaml
from charms import layer
from charms.reactive import set_flag, clear_flag, when, when_not, hookenv, endpoint_from_name


@when('charm.started')
def charm_ready():
    layer.status.active('')


@when('layer.docker-resource.oci-image.changed', 'config.changed')
def update_image():
    clear_flag('charm.started')


@when('layer.docker-resource.oci-image.available', 'pipelines-api.available', 'minio.available')
@when_not('charm.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')
    service_name = hookenv.service_name()

    api = endpoint_from_name('pipelines-api').services()[0]
    minio = endpoint_from_name('minio').services()[0]['hosts'][0]

    ui_port = hookenv.config('ui-port')
    proxy_port = hookenv.config('proxy-port')

    layer.caas_base.pod_spec_set(
        {
            'service': {
                'annotations': {
                    'getambassador.io/config': yaml.dump_all(
                        [
                            {
                                'apiVersion': 'ambassador/v0',
                                'kind': 'Mapping',
                                'name': 'pipeline-ui',
                                'prefix': '/pipeline',
                                'rewrite': '/pipeline',
                                'service': f'{service_name}:{ui_port}',
                                'use_websocket': True,
                                'timeout_ms': 30000,
                            },
                            {
                                'apiVersion': 'ambassador/v0',
                                'kind': 'Mapping',
                                'name': 'pipeline-ui-apis',
                                'prefix': '/apis',
                                'rewrite': '/apis',
                                'service': f'{service_name}:{proxy_port}',
                                'use_websocket': True,
                                'timeout_ms': 30000,
                            },
                        ]
                    )
                }
            },
            'containers': [
                {
                    'name': 'pipelines-ui',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'config': {
                        'ML_PIPELINE_SERVICE_HOST': api['service_name'],
                        'ML_PIPELINE_SERVICE_PORT': api['hosts'][0]['port'],
                        'MINIO_HOST': minio['hostname'],
                        'MINIO_PORT': minio['port'],
                        'MINIO_NAMESPACE': os.environ['JUJU_MODEL_NAME'],
                    },
                    'ports': [
                        {'name': 'ui', 'containerPort': ui_port},
                        {'name': 'api-proxy', 'containerPort': proxy_port},
                    ],
                }
            ],
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
