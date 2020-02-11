from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import hook, clear_flag, set_flag, when, when_any, when_not, endpoint_from_name


@hook('upgrade-charm')
def upgrade_charm():
    clear_flag('charm.started')


@when('charm.started')
def charm_ready():
    layer.status.active('')


@when('metadata-grpc.available')
def configure_http(http):
    http.configure(port=hookenv.config('port'), hostname=hookenv.application_name())


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
    db_name = hookenv.config('database-name')

    layer.caas_base.pod_spec_set(
        spec={
            'version': 2,
            'containers': [
                {
                    'name': 'metadata-grpc',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'command': ['/bin/metadata_store_server'],
                    'args': [
                        f"--grpc_port={port}",
                        f"--mysql_config_database={db_name}",
                        f"--mysql_config_host={mysql.host()}",
                        f"--mysql_config_port={mysql.port()}",
                        "--mysql_config_user=root",
                        f"--mysql_config_password={mysql.root_password()}",
                    ],
                    'ports': [{'name': 'grpc', 'containerPort': port}],
                }
            ],
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
