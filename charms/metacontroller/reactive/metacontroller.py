from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import set_flag, clear_flag, when, when_not


@when('charm.started')
def charm_ready():
    layer.status.active('')


@when('layer.docker-resource.oci-image.changed', 'config.changed')
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
            ]
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
