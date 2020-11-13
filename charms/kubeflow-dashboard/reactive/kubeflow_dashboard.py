import os
from pathlib import Path

import yaml

from charms import layer
from charms.reactive import (
    clear_flag,
    endpoint_from_name,
    hook,
    hookenv,
    set_flag,
    when,
    when_any,
    when_not,
)


@hook('upgrade-charm')
def upgrade_charm():
    clear_flag('charm.started')


@when('charm.started')
def charm_ready():
    layer.status.active('')


@when_any('layer.docker-resource.oci-image.changed', 'config.changed')
def update_image():
    clear_flag('charm.started')


@when('endpoint.service-mesh.joined')
def configure_mesh():
    endpoint_from_name('service-mesh').add_route(
        prefix='/', service=hookenv.service_name(), port=hookenv.config('port')
    )


@when('layer.docker-resource.oci-image.available', 'kubeflow-profiles.available')
@when_not('charm.started')
def start_charm():
    if not hookenv.is_leader():
        hookenv.log("This unit is not a leader.")
        return False

    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')
    model = os.environ['JUJU_MODEL_NAME']

    profiles = endpoint_from_name('kubeflow-profiles').services()[0]
    profiles_service = profiles['service_name']

    port = hookenv.config('port')
    profile = hookenv.config('profile')

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
            'serviceAccount': {
                'global': True,
                'rules': [
                    {
                        'apiGroups': [''],
                        'resources': ['events', 'namespaces', 'nodes'],
                        'verbs': ['get', 'list', 'watch'],
                    },
                    {
                        'apiGroups': ['', 'app.k8s.io'],
                        'resources': ['applications', 'pods', 'pods/exec', 'pods/log'],
                        'verbs': ['get', 'list', 'watch'],
                    },
                    {'apiGroups': [''], 'resources': ['secrets'], 'verbs': ['get']},
                ],
            },
            'containers': [
                {
                    'name': 'kubeflow-dashboard',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'config': {
                        'USERID_HEADER': 'kubeflow-userid',
                        'USERID_PREFIX': '',
                        'PROFILES_KFAM_SERVICE_HOST': f'{profiles_service}.{model}',
                        'REGISTRATION_FLOW': hookenv.config('registration-flow'),
                    },
                    'ports': [{'name': 'ui', 'containerPort': port}],
                    'kubernetes': {
                        'livenessProbe': {
                            'httpGet': {'path': '/healthz', 'port': 8082},
                            'initialDelaySeconds': 30,
                            'periodSeconds': 30,
                        }
                    },
                }
            ],
        },
        {
            'kubernetesResources': {
                'customResourceDefinitions': {
                    crd['metadata']['name']: crd['spec']
                    for crd in yaml.safe_load_all(Path("files/crds.yaml").read_text())
                },
                'customResources': {
                    'profiles.kubeflow.org': [
                        {
                            'apiVersion': 'kubeflow.org/v1beta1',
                            'kind': 'Profile',
                            'metadata': {'name': profile},
                            'spec': {'owner': {'kind': 'User', 'name': profile}},
                        }
                    ]
                },
            }
        },
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
