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

    model = hookenv.config('model')
    model_conf = hookenv.config('model-conf')
    grpc_port = hookenv.config('grpc-port')
    rest_port = hookenv.config('rest-port')

    if model:
        hookenv.log(f'Serving single model `{model}`')
        path, name = model.rsplit('/', maxsplit=1)
        command_args = [f'--model_name={name}', f'--model_base_path=/models/{path}']
    else:
        hookenv.log(f'Serving models from {model_conf}')
        command_args = [f'--model_config_file=/models/{model_conf}']

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
            'containers': [
                {
                    'name': 'tf-serving',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'command': [
                        '/usr/bin/tensorflow_model_server',
                        f'--port={grpc_port}',
                        f'--rest_api_port={rest_port}',
                    ]
                    + command_args,
                    'ports': [
                        {'name': 'tf-serving-grpc', 'containerPort': grpc_port},
                        {'name': 'tf-serving-rest', 'containerPort': rest_port},
                    ],
                }
            ],
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
