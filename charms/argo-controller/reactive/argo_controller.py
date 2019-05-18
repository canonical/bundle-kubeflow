from pathlib import Path

import yaml
from charms import layer
from charms.reactive import clear_flag, set_flag, when, when_any, when_not


@when('charm.argo-controller.started')
def charm_ready():
    layer.status.active('')


@when_any('layer.docker-resource.oci-image.changed')
def update_image():
    clear_flag('charm.argo-controller.started')


@when('layer.docker-resource.oci-image.available')
@when_not('charm.argo-controller.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    crd = yaml.safe_load(Path("files/crd-v1alpha1.yaml").read_text())

    layer.caas_base.pod_spec_set(
        {
            'containers': [
                {
                    'name': 'argo-controller',
                    'command': ['workflow-controller'],
                    'args': ['--configmap', 'argo-controller-configmap-config'],
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'ports': [{'name': 'dummy', 'containerPort': 9999}],
                    'config': {'ARGO_NAMESPACE': 'kubeflow'},
                    'files': [
                        {
                            'name': 'configmap',
                            'mountPath': '/config-map.yaml',
                            'files': {'config': Path('files/config-map.yaml').read_text()},
                        }
                    ],
                }
            ],
            'customResourceDefinitions': {crd['metadata']['name']: crd['spec']},
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.argo-controller.started')
