from pathlib import Path
import os

import yaml

from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import clear_flag, hook, set_flag, when, when_any, when_not


@hook('upgrade-charm')
def upgrade_charm():
    clear_flag('charm.started')


@when('charm.started')
def charm_ready():
    layer.status.active('')


@when_any(
    'layer.docker-resource.oci-image.changed',
    'config.changed',
    'endpoint.service-mesh.changed',
)
def update_image():
    clear_flag('charm.started')
    clear_flag('endpoint.service-mesh.changed')


@when('layer.docker-resource.oci-image.available')
@when_not('charm.started')
def start_charm():
    if not hookenv.is_leader():
        hookenv.log("This unit is not a leader.")
        return False

    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')
    model = os.environ['JUJU_MODEL_NAME']

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
            'serviceAccount': {
                'global': True,
                'rules': [
                    {
                        'apiGroups': ['apps'],
                        'resources': ['statefulsets', 'deployments'],
                        'verbs': ['*'],
                    },
                    {
                        'apiGroups': [''],
                        'resources': ['pods'],
                        'verbs': ['get', 'list', 'watch'],
                    },
                    {
                        'apiGroups': [''],
                        'resources': ['services'],
                        'verbs': ['*'],
                    },
                    {
                        'apiGroups': [''],
                        'resources': ['events'],
                        'verbs': ['get', 'list', 'watch', 'create'],
                    },
                    {
                        'apiGroups': ['kubeflow.org'],
                        'resources': ['notebooks', 'notebooks/status', 'notebooks/finalizers'],
                        'verbs': ['*'],
                    },
                    {
                        'apiGroups': ['networking.istio.io'],
                        'resources': ['virtualservices'],
                        'verbs': ['*'],
                    },
                ],
            },
            'containers': [
                {
                    'name': 'jupyter-controller',
                    'command': ['/manager'],
                    'config': {
                        'USE_ISTIO': str(hookenv.is_relation_made('service-mesh')).lower(),
                        'ISTIO_GATEWAY': f'{model}/kubeflow-gateway',
                        'ENABLE_CULLING': hookenv.config('enable-culling'),
                    },
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                }
            ],
        },
        {
            'kubernetesResources': {
                "customResourceDefinitions": {
                    crd["metadata"]["name"]: crd["spec"]
                    for crd in yaml.safe_load_all(Path("files/crds.yaml").read_text())
                },
                'serviceAccounts': [
                    {
                        'name': 'jupyter-notebook',
                        'rules': [
                            {
                                'apiGroups': [''],
                                'resources': ['pods', 'pods/log', 'secrets', 'services'],
                                'verbs': ['*'],
                            },
                            {
                                'apiGroups': ['', 'apps', 'extensions'],
                                'resources': ['deployments', 'replicasets'],
                                'verbs': ['*'],
                            },
                            {'apiGroups': ['kubeflow.org'], 'resources': ['*'], 'verbs': ['*']},
                            {'apiGroups': ['batch'], 'resources': ['jobs'], 'verbs': ['*']},
                        ],
                    }
                ],
            }
        },
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
