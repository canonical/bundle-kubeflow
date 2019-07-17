import os

from charms import layer
from charms.reactive import set_flag, clear_flag
from charms.reactive import when, when_not


@when('charm.cert-manager-cainjector.started')
def charm_ready():
    layer.status.active('')


@when('layer.docker-resource.oci-image.changed', 'config.changed')
def update_image():
    clear_flag('charm.cert-manager-cainjector.started')


@when('layer.docker-resource.oci-image.available')
@when_not('charm.cert-manager-cainjector.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    namespace = os.environ['JUJU_MODEL_NAME']

    layer.caas_base.pod_spec_set(
        {
            'containers': [
                {
                    'name': 'cert-manager-cainjector',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'args': ['--v=2', f'--leader-election-namespace={namespace}'],
                    'ports': [{'name': 'dummy', 'containerPort': 9999}],
                    'config': {'POD_NAMESPACE': namespace},
                }
            ]
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.cert-manager-cainjector.started')
