import os

from charms import layer
from charms.reactive import set_flag, clear_flag, when, when_not


@when('charm.kubeflow-ambassador.started')
def charm_ready():
    layer.status.active('')


@when('layer.docker-resource.oci-image.changed')
def update_image():
    clear_flag('charm.kubeflow-ambassador.started')


@when('layer.docker-resource.oci-image.available')
@when_not('charm.kubeflow-ambassador.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    layer.caas_base.pod_spec_set(
        {
            'containers': [
                {
                    'name': 'ambassador',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'command': [],
                    'ports': [{'name': 'ambassador', 'containerPort': 80}],
                    'config': {
                        'AMBASSADOR_NAMESPACE': os.environ['JUJU_MODEL_NAME'],
                        'AMBASSADOR_SINGLE_NAMESPACE': 'true',
                    },
                    'livenessProbe': {
                        'httpGet': {'path': '/ambassador/v0/check_alive', 'port': 8877},
                        'initialDelaySeconds': 30,
                        'periodSeconds': 30,
                    },
                    'readinessProbe': {
                        'httpGet': {'path': '/ambassador/v0/check_ready', 'port': 8877},
                        'initialDelaySeconds': 30,
                        'periodSeconds': 30,
                    },
                }
            ]
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.kubeflow-ambassador.started')
