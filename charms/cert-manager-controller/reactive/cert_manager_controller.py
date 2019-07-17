import os

from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import set_flag, clear_flag
from charms.reactive import when, when_not


@when('charm.cert-manager-controller.started')
def charm_ready():
    layer.status.active('')


@when('layer.docker-resource.oci-image.changed', 'config.changed')
def update_image():
    clear_flag('charm.cert-manager-controller.started')


@when('layer.docker-resource.oci-image.available')
@when_not('charm.cert-manager-controller.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    namespace = os.environ['JUJU_MODEL_NAME']

    layer.caas_base.pod_spec_set(
        {
            'containers': [
                {
                    'name': 'https://34.235.133.110:17070/gui/u/admin/kubeflow-controller',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'args': [
                        f'--cluster-resource-namespace={namespace}',
                        f'--leader-election-namespace={namespace}',
                    ],
                    'ports': [{'name': 'http', 'containerPort': hookenv.config('port')}],
                }
            ]
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.cert-manager-controller.started')
