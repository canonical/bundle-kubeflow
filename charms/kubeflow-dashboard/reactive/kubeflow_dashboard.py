import os

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


@when('layer.docker-resource.oci-image.available', 'kubeflow-profiles.available')
@when_not('charm.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')
    service_name = hookenv.service_name()
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
            'service': {
                'annotations': {
                    'getambassador.io/config': yaml.dump_all(
                        [
                            {
                                'apiVersion': 'ambassador/v0',
                                'kind': 'Mapping',
                                'name': 'dashboard-mapping',
                                'prefix': '/',
                                'rewrite': '/',
                                'service': f'{service_name}:{port}',
                                'timeout_ms': 30000,
                            }
                        ]
                    )
                }
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
                        'USERID_HEADER': '',
                        'USERID_PREFIX': '',
                        'PROFILES_KFAM_SERVICE_HOST': f'{profiles_service}.{model}',
                    },
                    'ports': [{'name': 'ui', 'containerPort': port}],
                }
            ],
        },
        {
            'kubernetesResources': {
                'customResources': {
                    'profiles.kubeflow.org': [
                        {
                            'apiVersion': 'kubeflow.org/v1alpha1',
                            'kind': 'Profile',
                            'metadata': {'name': profile},
                            'spec': {'owner': {'kind': 'User', 'name': profile}},
                        }
                    ]
                }
            }
        },
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
