from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import set_flag, clear_flag, when, when_not


@when('charm.modeldb-store.started')
def charm_ready():
    layer.status.active('')


@when('layer.docker-resource.oci-image.changed', 'config.changed')
def update_image():
    clear_flag('charm.modeldb-store.started')


@when('layer.docker-resource.oci-image.available')
@when_not('charm.modeldb-store.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    port = hookenv.config('port')

    layer.caas_base.pod_spec_set(
        {
            'containers': [
                {
                    'name': 'modeldb-store',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'ports': [{'name': 'port', 'containerPort': port}],
                    'config': {'VERTA_ARTIFACT_CONFIG': '/config/config.yaml'},
                    'files': [
                        {
                            'name': 'config',
                            'mountPath': '/config/',
                            'files': {'config.yaml': hookenv.config('config')},
                        }
                    ],
                }
            ]
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.modeldb-store.started')
