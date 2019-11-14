from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import hook, set_flag, clear_flag, when, when_any, when_not, endpoint_from_name


@hook('upgrade-charm')
def upgrade_charm():
    clear_flag('charm.started')


@when('charm.started')
def charm_ready():
    layer.status.active('')


@when_any('layer.docker-resource.oci-image.changed', 'config.changed', 'mysql.changed')
def update_image():
    clear_flag('charm.started')


@when('layer.docker-resource.oci-image.available', 'mysql.available')
@when_not('charm.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    mysql = endpoint_from_name('mysql')

    port = hookenv.config('port')

    layer.caas_base.pod_spec_set(
        {
            'containers': [
                {
                    'name': 'katib-manager',
                    'command': ["./katib-manager"],
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'ports': [{'name': 'manager', 'containerPort': port}],
                    'config': {
                        'DB_NAME': 'mysql',
                        'DB_PASSWORD': mysql.root_password(),
                        'MYSQL_HOST': mysql.host(),
                        'MYSQL_PORT': mysql.port(),
                    },
                    'livenessProbe': {
                        'exec': {'command': ["/bin/grpc_health_probe", f"-addr=:{port}"]},
                        'initialDelaySeconds': 10,
                    },
                    'readinessProbe': {
                        'exec': {'command': ["/bin/grpc_health_probe", f"-addr=:{port}"]},
                        'initialDelaySeconds': 5,
                        'periodSeconds': 60,
                        'failureThreshold': 5,
                    },
                }
            ]
        }
    )

    layer.status.maintenance('creating container')
    clear_flag('mysql.changed')
    set_flag('charm.started')
