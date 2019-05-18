from charms import layer
from charms.reactive import set_flag, clear_flag, when, when_not, hookenv


@when('charm.minio.started')
def charm_ready():
    layer.status.active('')


@when('minio.available')
def configure_minio(http):
    http.configure(port=hookenv.config('port'))


@when('layer.docker-resource.oci-image.changed', 'config.changed')
def update_image():
    clear_flag('charm.minio.started')


@when('layer.docker-resource.oci-image.available')
@when_not('charm.minio.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    layer.caas_base.pod_spec_set(
        {
            'containers': [
                {
                    'name': 'minio',
                    'args': ['server', '/data'],
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'ports': [{'name': 'minio', 'containerPort': hookenv.config('port')}],
                    'config': {
                        'MINIO_ACCESS_KEY': hookenv.config('access-key'),
                        'MINIO_SECRET_KEY': hookenv.config('secret-key'),
                    },
                }
            ]
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.minio.started')
