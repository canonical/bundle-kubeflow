from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import set_flag, clear_flag, when, when_not, endpoint_from_name


@when('charm.started')
def charm_ready():
    layer.status.active('')


@when('layer.docker-resource.oci-image.changed')
def update_image():
    clear_flag('charm.started')


@when(
    'layer.docker-resource.manager-image.available',
    'layer.docker-resource.restful-image.available',
    'mysql.connected',
)
@when_not('charm.started')
def start_charm():
    layer.status.maintenance('configuring container')

    manager_image = layer.docker_resource.get_info('manager-image')
    restful_image = layer.docker_resource.get_info('restful-image')

    mysql = endpoint_from_name('mysql')

    manager_port = hookenv.config('manager-port')
    restful_port = hookenv.config('restful-port')

    layer.caas_base.pod_spec_set(
        {
            'containers': [
                {
                    'name': 'katib-manager',
                    'command': ["./katib-manager"],
                    'imageDetails': {
                        'imagePath': manager_image.registry_path,
                        'username': manager_image.username,
                        'password': manager_image.password,
                    },
                    'ports': [{'name': 'manager', 'containerPort': manager_port}],
                    'config': {'MYSQL_ROOT_PASSWORD': mysql.password()},
                    'livenessProbe': {
                        'exec': {'command': ["/bin/grpc_health_probe", f"-addr=:{manager_port}"]},
                        'initialDelaySeconds': 10,
                    },
                    'readinessProbe': {
                        'exec': {'command': ["/bin/grpc_health_probe", f"-addr=:{manager_port}"]},
                        'initialDelaySeconds': 5,
                    },
                },
                {
                    'name': 'katib-manager-rest',
                    'command': ["./katib-manager-rest"],
                    'imageDetails': {
                        'imagePath': restful_image.registry_path,
                        'username': restful_image.username,
                        'password': restful_image.password,
                    },
                    'ports': [{'name': 'restful', 'containerPort': restful_port}],
                },
            ]
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
