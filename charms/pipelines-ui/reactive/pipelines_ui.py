import yaml
from charms import layer
from charms.reactive import set_flag, clear_flag, when, when_not, hookenv


@when('charm.pipelines-ui.started')
def charm_ready():
    layer.status.active('')


@when(
    'layer.docker-resource.oci-image.changed',
    'config.changed',
)
def update_image():
    clear_flag('charm.pipelines-ui.started')


@when(
    'layer.docker-resource.oci-image.available',
    'pipelines-api.available',
)
@when_not('charm.pipelines-ui.started')
def start_charm(api):
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')
    service_name = hookenv.service_name()

    ui_port = hookenv.config('ui-port')
    proxy_port = hookenv.config('proxy-port')

    layer.caas_base.pod_spec_set({
        'service': {'annotations': {
            'getambassador.io/config': yaml.dump_all([
                {
                    'apiVersion': 'ambassador/v0',
                    'kind':  'Mapping',
                    'name':  'pipeline-ui',
                    'prefix': '/pipeline',
                    'rewrite': '/pipeline',
                    'service': f'{service_name}:{ui_port}',
                    'use_websocket': True,
                    'timeout_ms': 30000,
                },
                {
                    'apiVersion': 'ambassador/v0',
                    'kind':  'Mapping',
                    'name':  'pipeline-ui-apis',
                    'prefix': '/apis',
                    'rewrite': '/apis',
                    'service': f'{service_name}:{proxy_port}',
                    'use_websocket': True,
                    'timeout_ms': 30000,
                },
            ]),
        }},
        'containers': [
            {
                'name': 'pipelines-ui',
                'imageDetails': {
                    'imagePath': image_info.registry_path,
                    'username': image_info.username,
                    'password': image_info.password,
                },
                'config': {
                    'ML_PIPELINE_SERVICE_HOST': api.services()[0]['service_name'],
                    'ML_PIPELINE_SERVICE_PORT': api.services()[0]['hosts'][0]['port'],
                },
                'ports': [
                    {
                        'name': 'ui',
                        'containerPort': ui_port,
                    },
                    {
                        'name': 'api-proxy',
                        'containerPort': proxy_port,
                    },
                ],
            },
        ],
    })

    layer.status.maintenance('creating container')
    set_flag('charm.pipelines-ui.started')
