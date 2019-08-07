from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import set_flag, clear_flag, when, when_not, endpoint_from_name


@when('charm.started')
def charm_ready():
    layer.status.active('')


@when('layer.docker-resource.oci-image.changed')
def update_image():
    clear_flag('charm.started')


@when('layer.docker-resource.oci-image.available', 'mysql.connected')
@when_not('charm.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    mysql = endpoint_from_name('mysql')

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
                    'ports': [{'name': 'probe', 'containerPort': 6789}],
                    'config': {'MYSQL_ROOT_PASSWORD': mysql.password()},
                    'livenessProbe': {
                        'exec': {'command': ["/bin/grpc_health_probe", "-addr=:6789"]},
                        'initialDelaySeconds': 10,
                    },
                    'readinessProbe': {
                        'exec': {'command': ["/bin/grpc_health_probe", "-addr=:6789"]},
                        'initialDelaySeconds': 5,
                    },
                },
                {
                    'name': 'katib-manager-rest',
                    'command': ["./katib-manager-rest"],
                    'image': 'gcr.io/kubeflow-images-public/katib/v1alpha2/katib-manager-rest:v0.1.2-alpha-289-g14dad8b',
                    'ports': [{'name': 'rest', 'containerPort': 80}],
                },
            ]
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
