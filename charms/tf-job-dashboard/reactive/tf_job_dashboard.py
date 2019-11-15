import os

import yaml
from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import hook, clear_flag, set_flag, when_any, when, when_not


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

    port = hookenv.config('port')

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
            'serviceAccount': {
                'rules': [
                    {
                        'apiGroups': ['tensorflow.org', 'kubeflow.org'],
                        'resources': ['tfjobs', 'tfjobs/status'],
                        'verbs': ['*'],
                    },
                    {
                        'apiGroups': ['apiextensions.k8s.io'],
                        'resources': ['customresourcedefinitions'],
                        'verbs': ['*'],
                    },
                    {
                        'apiGroups': ['storage.k8s.io'],
                        'resources': ['storageclasses'],
                        'verbs': ['*'],
                    },
                    {'apiGroups': ['batch'], 'resources': ['jobs'], 'verbs': ['*']},
                    {
                        'apiGroups': [''],
                        'resources': [
                            'configmaps',
                            'pods',
                            'services',
                            'endpoints',
                            'persistentvolumeclaims',
                            'events',
                            'pods/log',
                            'namespaces',
                        ],
                        'verbs': ['*'],
                    },
                    {
                        'apiGroups': ['apps', 'extensions'],
                        'resources': ['deployments'],
                        'verbs': ['*'],
                    },
                ]
            },
            'service': {
                'annotations': {
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
            },
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
                    'config': {'KUBEFLOW_NAMESPACE': os.environ['JUJU_MODEL_NAME']},
                }
            ],
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
