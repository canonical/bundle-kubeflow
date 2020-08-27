from pathlib import Path

import yaml

from charms import layer
from charms.reactive import clear_flag, hook, hookenv, set_flag, when, when_any, when_not


@hook('upgrade-charm')
def upgrade_charm():
    clear_flag('charm.started')


@when('charm.started')
def charm_ready():
    layer.status.active('')


@when('kubeflow-profiles.available')
def configure_http(http):
    http.configure(port=hookenv.config('port'), hostname=hookenv.application_name())


@when_any(
    'layer.docker-resource.profile-image.changed',
    'layer.docker-resource.kfam-image.changed',
    'config.changed',
)
def update_image():
    clear_flag('charm.started')


@when('layer.docker-resource.profile-image.available', 'layer.docker-resource.kfam-image.available')
@when_not('charm.started')
def start_charm():
    if not hookenv.is_leader():
        hookenv.log("This unit is not a leader.")
        return False

    layer.status.maintenance('configuring container')

    profile_info = layer.docker_resource.get_info('profile-image')
    kfam_info = layer.docker_resource.get_info('kfam-image')

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
            'serviceAccount': {
                'global': True,
                'rules': [
                    {'apiGroups': ['*'], 'resources': ['*'], 'verbs': ['*']},
                    {'nonResourceURLs': ['*'], 'verbs': ['*']},
                ],
            },
            'containers': [
                {
                    'name': 'kubeflow-profiles',
                    'imageDetails': {
                        'imagePath': profile_info.registry_path,
                        'username': profile_info.username,
                        'password': profile_info.password,
                    },
                    'command': ['/manager'],
                    'args': [
                        '-userid-header',
                        'kubeflow-userid',
                        '-userid-prefix',
                        '',
                        '-workload-identity',
                        '',
                    ],
                    'ports': [
                        {'name': 'manager', 'containerPort': hookenv.config('manager-port')}
                    ],
                    'kubernetes': {
                        'livenessProbe': {
                            'httpGet': {
                                'path': '/metrics',
                                'port': hookenv.config('manager-port'),
                            },
                            'initialDelaySeconds': 30,
                            'periodSeconds': 30,
                        }
                    },
                },
                {
                    'name': 'kubeflow-kfam',
                    'imageDetails': {
                        'imagePath': kfam_info.registry_path,
                        'username': kfam_info.username,
                        'password': kfam_info.password,
                    },
                    'command': ['/access-management'],
                    'args': [
                        '-cluster-admin',
                        'admin',
                        '-userid-header',
                        'kubeflow-userid',
                        '-userid-prefix',
                        '',
                    ],
                    'ports': [{'name': 'http', 'containerPort': hookenv.config('port')}],
                    'kubernetes': {
                        'livenessProbe': {
                            'httpGet': {'path': '/metrics', 'port': hookenv.config('port')},
                            'initialDelaySeconds': 30,
                            'periodSeconds': 30,
                        }
                    },
                },
            ],
        },
        {
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
