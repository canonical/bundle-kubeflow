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
    'layer.docker-resource.oci-image.available', 'metadata-api.available', 'metadata-grpc.available'
)
@when_not('charm.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')
    service_name = hookenv.service_name()

    api = endpoint_from_name('metadata-api').services()[0]
    grpc = endpoint_from_name('metadata-grpc').services()[0]

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
                                'name': 'metadata-ui',
                                'prefix': '/metadata',
                                'rewrite': '/metadata',
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
                    'name': 'metadata-ui',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'ports': [{'name': 'http', 'containerPort': port}],
                    'config': {
                        'METADATA_SERVICE_SERVICE_HOST': api['service_name'],
                        'METADATA_SERVICE_SERVICE_PORT': api['hosts'][0]['port'],
                        'METADATA_ENVOY_SERVICE_SERVICE_HOST': grpc['service_name'],
                        'METADATA_ENVOY_SERVICE_SERVICE_PORT': grpc['hosts'][0]['port'],
                    },
                }
            ],
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
