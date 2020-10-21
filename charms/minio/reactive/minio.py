from charms import layer
from charms.reactive import hook, set_flag, clear_flag, when, when_any, when_not, hookenv
from pathlib import Path
from string import ascii_uppercase, digits
from random import choices


@hook('upgrade-charm')
def upgrade_charm():
    clear_flag('charm.started')


@when('charm.started')
def charm_ready():
    layer.status.active('')


@when('endpoint.minio.joined')
def configure_minio(gipup):
    if not Path('/run/password').exists():
        Path('/run/password').write_text(''.join(choices(ascii_uppercase + digits, k=30)))

    gipup.publish_info(
        port=hookenv.config('port'),
        ip=hookenv.application_name(),
        user='minio',
        password=Path('/run/password').read_text(),
    )


@when_any('layer.docker-resource.oci-image.changed', 'config.changed')
def update_image():
    clear_flag('charm.started')


@when('layer.docker-resource.oci-image.available')
@when_not('charm.started')
def start_charm():
    if not hookenv.is_leader():
        hookenv.log("This unit is not a leader.")
        return False

    layer.status.maintenance('configuring container')

    if not Path('/run/password').exists():
        Path('/run/password').write_text(''.join(choices(ascii_uppercase + digits, k=30)))

    image_info = layer.docker_resource.get_info('oci-image')
    config = dict(hookenv.config())

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
            'containers': [
                {
                    'name': 'minio',
                    'args': ['server', '/data'],
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'ports': [{'name': 'minio', 'containerPort': config['port']}],
                    'config': {
                        'MINIO_ACCESS_KEY': config['access-key'],
                        'MINIO_SECRET_KEY': Path('/run/password').read_text(),
                    },
                }
            ],
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
