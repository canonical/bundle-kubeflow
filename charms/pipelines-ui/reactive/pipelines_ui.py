import os

import yaml
from charms import layer
from charms.reactive import (
    hook,
    set_flag,
    clear_flag,
    when,
    when_any,
    when_not,
    hookenv,
    endpoint_from_name,
)


@hook('upgrade-charm')
def upgrade_charm():
    clear_flag('charm.started')


@when('charm.started')
def charm_ready():
    layer.status.active('')


@when_any('layer.docker-resource.oci-image.changed', 'config.changed')
def update_image():
    clear_flag('charm.started')


@when(
    'layer.docker-resource.oci-image.available', 'pipelines-api.available', 'endpoint.minio.joined'
)
@when_not('charm.started')
def start_charm():
    if not hookenv.is_leader():
        hookenv.log("This unit is not a leader.")
        return False

    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')
    service_name = hookenv.service_name()

    api = endpoint_from_name('pipelines-api').services()[0]

    try:
        minio = endpoint_from_name('minio').mailman3()[0]
    except IndexError:
        layer.status.blocked('Waiting for minio relation.')
        return False

    if minio['ip'] is None:
        layer.status.blocked("Waiting for full minio relation.")
        return False

    port = hookenv.config('port')

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
            'serviceAccount': {
                'rules': [
                    {
                        'apiGroups': [''],
                        'resources': ['pods', 'pods/log'],
                        'verbs': ['create', 'get', 'list'],
                    },
                    {
                        'apiGroups': ['kubeflow.org'],
                        'resources': ['viewers'],
                        'verbs': ['create', 'get', 'list', 'watch', 'delete'],
                    },
                ]
            },
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
                    'name': 'pipelines-ui',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'config': {
                        'ML_PIPELINE_SERVICE_HOST': api['service_name'],
                        'ML_PIPELINE_SERVICE_PORT': api['hosts'][0]['port'],
                        'MINIO_HOST': minio['ip'],
                        'MINIO_PORT': minio['port'],
                        'MINIO_NAMESPACE': os.environ['JUJU_MODEL_NAME'],
                        'ALLOW_CUSTOM_VISUALIZATIONS': True,
                    },
                    'ports': [{'name': 'ui', 'containerPort': port}],
                }
            ],
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
