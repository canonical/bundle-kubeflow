from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import set_flag, clear_flag, when, when_not


@when('charm.modeldb-backend.started')
def charm_ready():
    layer.status.active('')


@when('modeldb-backend.available')
def configure_http(http):
    http.configure(port=hookenv.config('http-port'), hostname=hookenv.application_name())


@when('layer.docker-resource.oci-image.changed', 'config.changed')
def update_image():
    clear_flag('charm.modeldb-backend.started')


@when('layer.docker-resource.oci-image.available')
@when_not('charm.modeldb-backend.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    grpc_port = hookenv.config('grpc-port')
    http_port = hookenv.config('http-port')

    layer.caas_base.pod_spec_set(
        {
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
                        'mariadb:3306 '
                        '--timeout=30 '
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
                            'files': {'config.yaml': hookenv.config('config')},
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
            ]
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.modeldb-backend.started')
