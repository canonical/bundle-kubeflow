import yaml
from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import set_flag, clear_flag, when, when_not


@when('charm.modeldb-ui.started')
def charm_ready():
    layer.status.active('')


@when('layer.docker-resource.oci-image.changed', 'config.changed')
def update_image():
    clear_flag('charm.modeldb-ui.started')


@when('layer.docker-resource.oci-image.available', 'modeldb-backend.available')
@when_not('charm.modeldb-ui.started')
def start_charm(backend):
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    port = hookenv.config('port')

    layer.caas_base.pod_spec_set(
        {
            'containers': [
                {
                    'name': 'modeldb-ui',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'ports': [{'name': 'port', 'containerPort': port}],
                    'config': {
                        'BACKEND_API_DOMAIN': backend.services()[0]['service_name'],
                        'BACKEND_API_PORT': backend.services()[0]['hosts'][0]['port'],
                    },
                }
            ]
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.modeldb-ui.started')
