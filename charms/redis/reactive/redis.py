from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import hook, set_flag, clear_flag, endpoint_from_flag, when, when_any, when_not


@hook('upgrade-charm')
def upgrade_charm():
    clear_flag('charm.started')


@when('charm.started')
def charm_ready():
    layer.status.active('')


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
            'containers': [
                {
                    'name': 'redis',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'ports': [{'name': 'redis', 'containerPort': port}],
                }
            ]
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')


@when('endpoint.db.joined')
def send_relation_info():
    client = endpoint_from_flag('endpoint.db.joined')
    random_unit = client.all_joined_units[0]
    client.configure(host=random_unit.received['ingress-address'], port=hookenv.config('port'))
