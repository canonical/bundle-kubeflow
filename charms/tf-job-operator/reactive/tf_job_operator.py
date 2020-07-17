import os
from pathlib import Path

import yaml
from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import hook, set_flag, clear_flag, when, when_any, when_not


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
    if not hookenv.is_leader():
        hookenv.log("This unit is not a leader.")
        return False

    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
            'serviceAccount': {
                'rules': [
                    {
                        'apiGroups': ['kubeflow.org'],
                        'resources': ['tfjobs', 'tfjobs/status', 'tfjobs/finalizers'],
                        'verbs': ['*'],
                    },
                    {
                        'apiGroups': ['apiextensions.k8s.io'],
                        'resources': ['customresourcedefinitions'],
                        'verbs': ['*'],
                    },
                    {
                        'apiGroups': [''],
                        'resources': ['pods', 'services', 'endpoints', 'events'],
                        'verbs': ['*'],
                    },
                    {
                        'apiGroups': ['apps', 'extensions'],
                        'resources': ['deployments'],
                        'verbs': ['*'],
                    },
                ]
            },
            'containers': [
                {
                    'name': 'tf-job-operator',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'args': ['--alsologtostderr', '-v=1', '--monitoring-port=8443'],
                    'config': {
                        'MY_POD_NAMESPACE': os.environ['JUJU_MODEL_NAME'],
                        'MY_POD_NAME': hookenv.service_name(),
                    },
                }
            ],
        },
        k8s_resources={
            'kubernetesResources': {
                'customResourceDefinitions': {
                    crd['metadata']['name']: crd['spec']
                    for crd in yaml.safe_load_all(Path("files/crds.yaml").read_text())
                }
            }
        },
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
