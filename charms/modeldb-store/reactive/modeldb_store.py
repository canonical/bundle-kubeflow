from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import hook, set_flag, clear_flag, when, when_any, when_not


@hook('upgrade-charm')
def upgrade_charm():
    clear_flag('charm.started')


@when('charm.started')
def charm_ready():
    layer.status.active('')


@when('modeldb-store.available')
def configure_http(http):
    http.configure(port=hookenv.config('port'), hostname=hookenv.application_name())


@when_any('layer.docker-resource.oci-image.changed', 'config.changed')
def update_image():
    clear_flag('charm.started')


@when('layer.docker-resource.oci-image.available')
@when_not('charm.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    port = hookenv.config('port')

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
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
            ],
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
