from pathlib import Path

from jinja2 import Template

from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import clear_flag, hook, set_flag, when, when_any, when_not, endpoint_from_name


@hook('upgrade-charm')
def upgrade_charm():
    clear_flag('charm.started')


@when('charm.started')
def charm_ready():
    layer.status.active('')


@when_any('layer.docker-resource.oci-image.changed', 'config.changed')
def update_image():
    clear_flag('charm.started')


@when('endpoint.service-mesh.joined')
def configure_mesh():
    endpoint_from_name('service-mesh').add_route(
        prefix='/ml_metadata.MetadataStoreService/',
        service=hookenv.service_name(),
        port=hookenv.config('port'),
    )


@when('layer.docker-resource.oci-image.available', 'metadata-grpc.available')
@when_not('charm.started')
def start_charm():
    if not hookenv.is_leader():
        hookenv.log("This unit is not a leader.")
        return False

    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    admin_port = hookenv.config('admin-port')
    port = hookenv.config('port')

    grpc = endpoint_from_name('metadata-grpc').services()[0]
    envoy_yaml = Template(Path('files/envoy.yaml.tmpl').read_text()).render(
        port=port,
        grpc_host=grpc['service_name'],
        grpc_port=grpc['hosts'][0]['port'],
        admin_port=admin_port,
    )

    layer.caas_base.pod_spec_set(
        spec={
            'version': 2,
            'containers': [
                {
                    'name': 'metadata-envoy',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'command': ['/usr/local/bin/envoy'],
                    'args': ['-c', '/config/envoy.yaml'],
                    'ports': [
                        {'name': 'grpc', 'containerPort': port},
                        {'name': 'admin', 'containerPort': admin_port},
                    ],
                    'files': [
                        {
                            'name': 'config',
                            'mountPath': '/config',
                            'files': {'envoy.yaml': envoy_yaml},
                        }
                    ],
                }
            ],
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
