from glob import glob
from pathlib import Path

import yaml
from charmhelpers.core import hookenv
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
    service_name = hookenv.service_name()

    port = hookenv.config('port')

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
            'serviceAccount': {
                'global': True,
                'rules': [
                    {
                        'apiGroups': [''],
                        'resources': ['namespaces'],
                        'verbs': ['get', 'list', 'create', 'delete'],
                    },
                    {
                        'apiGroups': ['kubeflow.org'],
                        'resources': ['notebooks', 'poddefaults'],
                        'verbs': ['get', 'list', 'create', 'delete'],
                    },
                    {
                        'apiGroups': [''],
                        'resources': ['persistentvolumeclaims'],
                        'verbs': ['create', 'delete', 'get', 'list'],
                    },
                    {
                        'apiGroups': ['storage.k8s.io'],
                        'resources': ['storageclasses'],
                        'verbs': ['get', 'list', 'watch'],
                    },
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
            },
            'service': {
                'annotations': {
                    'getambassador.io/config': yaml.dump_all(
                        [
                            {
                                'apiVersion': 'ambassador/v0',
                                'kind': 'Mapping',
                                'name': 'jupyter-web',
                                'prefix': '/jupyter/',
                                'service': f'{service_name}:{port}',
                                'timeout_ms': 30000,
                                'add_request_headers': {'x-forwarded-prefix': '/jupyter'},
                            }
                        ]
                    )
                }
            },
            'containers': [
                {
                    'name': 'jupyterhub',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'ports': [{'name': 'http', 'containerPort': port}],
                    'files': [
                        {
                            'name': 'configs',
                            'mountPath': '/etc/config',
                            'files': {
                                Path(filename).name: Path(filename).read_text()
                                for filename in glob('files/*')
                            },
                        }
                    ],
                }
            ],
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
