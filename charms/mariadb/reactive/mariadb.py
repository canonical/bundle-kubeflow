import pymysql
from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import set_flag, when, when_not, clear_flag


@when('charm.mariadb.started')
def charm_ready():
    layer.status.active('')


@when('layer.docker-resource.oci-image.changed', 'config.changed')
def update_image():
    clear_flag('charm.mariadb.started')


@when('layer.docker-resource.oci-image.available')
@when_not('charm.mariadb.started')
def configure_workload():
    layer.status.maintenance('starting workload')

    # fetch the info (registry path, auth info) about the image
    image_info = layer.docker_resource.get_info('oci-image')

    root_password = hookenv.config('root-password')

    if not root_password:
        layer.status.blocked('Setting a root password is required!')
        return False

    layer.caas_base.pod_spec_set(
        {
            'containers': [
                {
                    'name': 'mariadb',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'ports': [{'name': 'db', 'containerPort': hookenv.config('port')}],
                    'config': {'MYSQL_ROOT_PASSWORD': root_password},
                }
            ]
        }
    )

    layer.status.active('ready')
    set_flag('charm.mariadb.started')


@when('charm.mariadb.started')
@when_not('charm.mariadb.configured')
def configure_db():
    hookenv.log('Setting up mariadb')

    root_password = hookenv.config('root-password')
    database = hookenv.config('database')
    service = hookenv.service_name()

    if not database:
        set_flag('charm.mariadb.configured')
        return True

    try:
        connection = pymysql.connect(
            host=hookenv.service_name(), user='root', password=root_password, charset='utf8mb4'
        )
    except pymysql.err.MySQLError as err:
        hookenv.log(f'Got error while attempting to connect to {service}: {err}')
        return False

    try:
        hookenv.log(f'Creating database {database}')

        with connection.cursor() as cursor:
            # Create a new record
            cursor.execute(f'CREATE DATABASE IF NOT EXISTS {database}')
            cursor.execute(
                f"GRANT ALL PRIVILEGES ON {database}.* TO root@localhost IDENTIFIED BY '{root_password}'"
            )

        connection.commit()
    finally:
        connection.close()

    set_flag('charm.mariadb.configured')
