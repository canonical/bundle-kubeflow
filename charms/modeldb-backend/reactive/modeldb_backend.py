import yaml
from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import hook, set_flag, clear_flag, when, when_not, when_any, endpoint_from_name


@hook('upgrade-charm')
def upgrade_charm():
    clear_flag('charm.started')


@when('charm.started')
def charm_ready():
    layer.status.active('')


@when('modeldb-backend.available')
def configure_http(http):
    http.configure(port=hookenv.config('http-port'), hostname=hookenv.application_name())


@when_any('layer.docker-resource.oci-image.changed', 'mysql.changed', 'config.changed')
def update_image():
    clear_flag('charm.started')


@when('layer.docker-resource.oci-image.available', 'mysql.available', 'modeldb-store.available')
@when_not('charm.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    mysql = endpoint_from_name('mysql')
    store = endpoint_from_name('modeldb-store').services()[0]['hosts'][0]

    grpc_port = hookenv.config('grpc-port')
    http_port = hookenv.config('http-port')

    if not mysql.host():
        hookenv.log('Waiting for mysql connection information.')
        return

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
            'containers': [
                {
                    'name': 'modeldb-backend',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'command': ['bash'],
                    'args': [
                        '-c',
                        './wait-for-it.sh '
                        f'{mysql.host()}:{mysql.port()} '
                        '--timeout=10 '
                        '&& '
                        'java '
                        '-jar '
                        'modeldb-1.0-SNAPSHOT-client-build.jar ',
                    ],
                    'ports': [{'name': 'grpc-port', 'containerPort': grpc_port}],
                    'config': {'VERTA_MODELDB_CONFIG': '/config-backend/config.yaml'},
                    'files': [
                        {
                            'name': 'config',
                            'mountPath': '/config-backend/',
                            'files': {
                                'config.yaml': yaml.dump(
                                    {
                                        'grpcServer': {
                                            'host': hookenv.service_name(),
                                            'port': grpc_port,
                                        },
                                        'database': {
                                            'DBType': 'rdbms',
                                            'RdbConfiguration': {
                                                'RdbDatabaseName': mysql.database(),
                                                'RdbDriver': 'com.mysql.cj.jdbc.Driver',
                                                'RdbDialect': 'org.hibernate.dialect.MySQL5Dialect',
                                                'RdbUrl': f'jdbc:mysql://{mysql.host()}:{mysql.port()}',
                                                'RdbUsername': mysql.user(),
                                                'RdbPassword': mysql.password(),
                                            },
                                        },
                                        'artifactStore_grpcServer': {
                                            'host': store['hostname'],
                                            'port': int(store['port']),
                                        },
                                        'entities': {
                                            'projectEntity': 'Project',
                                            'experimentEntity': 'Experiment',
                                            'experimentRunEntity': 'ExperimentRun',
                                            'artifactStoreMappingEntity': 'ArtifactStoreMapping',
                                            'jobEntity': 'Job',
                                        },
                                        'authService': {'host': None, 'port': None},
                                    }
                                )
                            },
                        }
                    ],
                },
                {
                    'name': 'modeldb-backend-proxy',
                    'image': 'vertaaiofficial/modeldb-backend-proxy:kubeflow',
                    'command': ['/go/bin/proxy'],
                    'args': [
                        '-project_endpoint',
                        f'localhost:{grpc_port}',
                        '-experiment_endpoint',
                        f'localhost:{grpc_port}',
                        '-experiment_run_endpoint',
                        f'localhost:{grpc_port}',
                    ],
                    'ports': [{'name': 'http-port', 'containerPort': http_port}],
                },
            ],
        }
    )

    layer.status.maintenance('creating container')
    clear_flag('mysql.changed')
    set_flag('charm.started')
