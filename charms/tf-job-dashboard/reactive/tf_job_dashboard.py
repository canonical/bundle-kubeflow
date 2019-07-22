import os

import yaml
from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import clear_flag, is_flag_set, register_trigger, set_flag, when, when_not

register_trigger(when='endpoint.ambassador.joined', clear_flag='charm.tf-job-dashboard.started')
register_trigger(when_not='endpoint.ambassador.joined', clear_flag='charm.tf-job-dashboard.started')


@when('charm.tf-job-dashboard.started')
def charm_ready():
    layer.status.active('')


@when('layer.docker-resource.oci-image.changed', 'config.changed')
def update_image():
    clear_flag('charm.tf-job-dashboard.started')


@when('layer.docker-resource.oci-image.available')
@when_not('charm.tf-job-dashboard.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    port = hookenv.config('port')

    if is_flag_set('endpoint.ambassador.joined'):
        annotations = {
            'getambassador.io/config': yaml.dump_all(
                [
                    {
                        'apiVersion': 'ambassador/v0',
                        'kind': 'Mapping',
                        'name': 'tf_dashboard',
                        'prefix': '/tfjobs/',
                        'rewrite': '/tfjobs/',
                        'service': f'{hookenv.service_name()}:{port}',
                        'timeout_ms': 30000,
                    }
                ]
            )
        }
    else:
        annotations = {}

    layer.caas_base.pod_spec_set(
        {
            'service': {'annotations': annotations},
            'containers': [
                {
                    'name': 'tf-job-dashboard',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'command': ['/opt/tensorflow_k8s/dashboard/backend'],
                    'ports': [{'name': 'http', 'containerPort': port}],
                    'serviceAccountName': 'tf-job-dashboard',
                    'config': {'KUBEFLOW_NAMESPACE': os.environ['JUJU_MODEL_NAME']},
                }
            ],
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.tf-job-dashboard.started')
