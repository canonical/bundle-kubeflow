from charmhelpers.core import hookenv, host, unitdata
from charms.reactive import set_flag, when, when_all, when_any, when_not, endpoint_from_name

from charms import layer

import mysql.connector


@when('layer.docker-resource.oci-image.available')
@when_not('charm.mariadb.started')
def configure_workload():
    layer.status.maintenance('starting workload')

    config = hookenv.config()

    root_password = (unitdata.kv().get('charm.mariadb.root-password') or
                     config['root-password'] or
                     host.pwgen(32))

    # we need this later to connect to the DB, but
    # this is an insecure way to store it; unfortunately,
    # we don't have a secure way
    unitdata.kv().set('charm.mariadb.root-password', root_password)

    # fetch the info (registry path, auth info) about the image
    image_info = layer.docker_resource.get_info('oci-image')

    # this can also be handed raw YAML, so some charm authors
    # choose to use templated YAML in a file instead
    layer.caas_base.pod_spec_set({
        'containers': [
            {
                'name': 'mariadb',
                'imageDetails': {
                    'imagePath': image_info.registry_path,
                    'username': image_info.username,
                    'password': image_info.password,
                },
                'command': [],
                'ports': [
                    {
                        'name': 'db',
                        'containerPort': 3306,
                    },
                ],
                'config': {
                    # juju doesn't support secrets yet
                    'MYSQL_ROOT_PASSWORD': '',
                    'MYSQL_ALLOW_EMPTY_PASSWORD': True,
                },
            },
        ],
    })

    layer.status.active('ready')
    set_flag('charm.mariadb.started')


@when_any('resource.mariadb.changed')
def update_image():
    # handle a new image resource becoming available
    configure_workload()


@when_all('charm.started',
          'endpoint.database.new-requests')
def handle_requests():
    db = endpoint_from_name('database')
    users = unitdata.kv().get('charm.users', {})
    root_password = unitdata.kv().get('charm.root-password')
    connection = mysql.connector.connect(user='root',
                                         password=root_password,
                                         host='mariadb')
    cursor = None
    try:
        cursor = connection.cursor()
        for request in db.new_requests:
            # determine db_name, username, and password for request,
            # generating each if needed
            if request.application_name not in users:
                users[request.application_name] = (host.pwgen(20),
                                                   host.pwgen(20))
            username, password = users[request.application_name]
            db_name = request.database_name or request.application_name

            # create the database and grant the user access
            layer.mariadb_k8s.create_database(cursor, db_name)
            if not layer.mariadb_k8s.grant_exists(cursor,
                                                  db_name,
                                                  username,
                                                  request.address):
                layer.mariadb_k8s.create_grant(cursor,
                                               db_name,
                                               username,
                                               password,
                                               request.address)

            # fulfill this request
            request.provide_database(db_name, username, password)
        cursor.commit()
    finally:
        if cursor:
            cursor.close()
        connection.close()


@when_all('charm.mariadb.started',
          'endpoint.database.new-departs')
def handle_departs():
    db = endpoint_from_name('database')
    root_password = unitdata.kv().get('charm.mariadb.root-password')
    connection = mysql.connector.connect(user='root',
                                         password=root_password,
                                         host='mariadb')
    cursor = None
    try:
        cursor = connection.cursor()
        for depart in db.new_departs:
            if depart.username:
                layer.mariadb_k8s.cleanup_grant(cursor,
                                                depart.username,
                                                depart.address)
            depart.ack()  # acknowledge this departure
        cursor.commit()
    finally:
        if cursor:
            cursor.close()
        connection.close()
