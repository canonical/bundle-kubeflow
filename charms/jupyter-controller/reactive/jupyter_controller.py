from pathlib import Path

import yaml
from charms import layer
from charms.reactive import hook, clear_flag, set_flag, when, when_any, when_not


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

    crd = yaml.safe_load(Path("files/crd-v1alpha1.yaml").read_text())

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
            'serviceAccount': {
                'rules': [
                    {
                        'apiGroups': ['apps'],
                        'resources': ['statefulsets', 'deployments'],
                        'verbs': ['*'],
                    },
                    {'apiGroups': [''], 'resources': ['pods'], 'verbs': ['get', 'list', 'watch']},
                    {'apiGroups': [''], 'resources': ['services'], 'verbs': ['*']},
                    {
                        'apiGroups': ['kubeflow.org'],
                        'resources': ['notebooks', 'notebooks/status'],
                        'verbs': ['*'],
                    },
                    {
                        'apiGroups': ['networking.istio.io'],
                        'resources': ['virtualservices'],
                        'verbs': ['*'],
                    },
                ]
            },
            'containers': [
                {
                    'name': 'jupyter-controller',
                    'command': ['/manager'],
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
                'customResourceDefinitions': {crd['metadata']['name']: crd['spec']},
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
