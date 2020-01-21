import os

from charms import layer
from charms.reactive import clear_flag, hook, set_flag, when, when_not


@hook('upgrade-charm')
def upgrade_charm():
    clear_flag('charm.started')


@when('charm.started')
def charm_ready():
    layer.status.active('')


@when('layer.docker-resource.oci-image.changed')
def update_image():
    clear_flag('charm.started')


@when('layer.docker-resource.oci-image.available')
@when_not('charm.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
            'serviceAccount': {
                'global': True,
                'rules': [
                    {
                        'apiGroups': [''],
                        'resources': [
                            'endpoints',
                            'namespaces',
                            'secrets',
                            'services',
                            'configmaps',
                        ],
                        'verbs': ['get', 'list', 'watch'],
                    },
                    {
                        'apiGroups': ['getambassador.io'],
                        'resources': ['*'],
                        'verbs': ['get', 'list', 'watch'],
                    },
                    {
                        'apiGroups': ['apiextensions.k8s.io'],
                        'resources': ['customresourcedefinitions'],
                        'verbs': ['get', 'list', 'watch'],
                    },
                    {
                        'apiGroups': ['networking.internal.knative.dev'],
                        'resources': ['clusteringresses', 'ingresses'],
                        'verbs': ['get', 'list', 'watch'],
                    },
                    {
                        'apiGroups': ['networking.internal.knative.dev'],
                        'resources': ['ingresses/status', 'clusteringresses/status'],
                        'verbs': ['update'],
                    },
                    {
                        'apiGroups': ['extensions'],
                        'resources': ['ingresses'],
                        'verbs': ['get', 'list', 'watch'],
                    },
                ],
            },
            'containers': [
                {
                    'name': 'ambassador',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'command': [],
                    'ports': [{'name': 'ambassador', 'containerPort': 80}],
                    'config': {'AMBASSADOR_NAMESPACE': os.environ['JUJU_MODEL_NAME']},
                    'kubernetes': {
                        'livenessProbe': {
                            'httpGet': {'path': '/ambassador/v0/check_alive', 'port': 8877},
                            'initialDelaySeconds': 30,
                            'periodSeconds': 30,
                        },
                        'readinessProbe': {
                            'httpGet': {'path': '/ambassador/v0/check_ready', 'port': 8877},
                            'initialDelaySeconds': 30,
                            'periodSeconds': 30,
                        },
                    },
                }
            ],
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
