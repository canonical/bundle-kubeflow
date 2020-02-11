from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import hook, clear_flag, set_flag, when, when_any, when_not, endpoint_from_name


@hook('upgrade-charm')
def upgrade_charm():
    clear_flag('charm.started')


@when('charm.started')
def charm_ready():
    layer.status.active('')


@when('metadata-api.available')
def configure_http(http):
    http.configure(port=hookenv.config('port'), hostname=hookenv.application_name())


@when_any('layer.docker-resource.oci-image.changed', 'config.changed', 'mysql.changed')
def update_image():
    clear_flag('charm.started')


@when('layer.docker-resource.oci-image.available', 'mysql.available')
@when_not('charm.started')
def start_charm():
    layer.status.maintenance('configuring container')

    mysql = endpoint_from_name('mysql')

    image_info = layer.docker_resource.get_info('oci-image')

    port = hookenv.config('port')
    db_name = hookenv.config('database-name')

    layer.caas_base.pod_spec_set(
        spec={
            'version': 2,
            'containers': [
                {
                    'name': 'metadata-api',
                    'command': [
                        "./server/server",
                        f"--http_port={port}",
                        f"--mysql_service_host={mysql.host()}",
                        f"--mysql_service_port={mysql.port()}",
                        "--mysql_service_user=root",
                        f"--mysql_service_password={mysql.root_password()}",
                        f"--mlmd_db_name={db_name}",
                    ],
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'ports': [{'name': 'http', 'containerPort': port}],
                    'config': {'MYSQL_ROOT_PASSWORD': mysql.root_password()},
                    'kubernetes': {
                        'readinessProbe': {
                            'httpGet': {
                                'path': '/api/v1alpha1/artifact_types',
                                'port': 'http',
                                'httpHeaders': [
                                    {'name': 'ContentType', 'value': 'application/json'}
                                ],
                            },
                            'initialDelaySeconds': 3,
                            'periodSeconds': 5,
                            'timeoutSeconds': 2,
                        }
                    },
                }
            ],
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
