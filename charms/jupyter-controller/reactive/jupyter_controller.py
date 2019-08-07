from pathlib import Path

import yaml
from charms import layer
from charms.reactive import clear_flag, set_flag, when, when_any, when_not


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

    crd = yaml.safe_load(Path("files/crd-v1alpha1.yaml").read_text())

    layer.caas_base.pod_spec_set(
        {
            'containers': [
                {
                    'name': 'jupyterhub',
                    'command': ['/manager'],
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'ports': [{'name': 'dummy', 'containerPort': 9999}],
                }
            ],
            'customResourceDefinitions': {crd['metadata']['name']: crd['spec']},
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
