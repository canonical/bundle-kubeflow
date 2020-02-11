import os

from charms import layer
from charms.reactive import hook, set_flag, clear_flag, when, when_not, endpoint_from_name


@hook('upgrade-charm')
def upgrade_charm():
    clear_flag('charm.started')


@when('charm.started')
def charm_ready():
    layer.status.active('')


@when('layer.docker-resource.oci-image.changed')
def update_image():
    clear_flag('charm.started')


@when('layer.docker-resource.oci-image.available', 'pipelines-api.available')
@when_not('charm.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    api = endpoint_from_name('pipelines-api').services()[0]['hosts'][0]['hostname']

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
            'serviceAccount': {
                'global': True,
                'rules': [
                    {
                        'apiGroups': ['argoproj.io'],
                        'resources': ['workflows'],
                        'verbs': ['get', 'list', 'watch'],
                    },
                    {
                        'apiGroups': ['kubeflow.org'],
                        'resources': ['scheduledworkflows'],
                        'verbs': ['get', 'list', 'watch'],
                    },
                ],
            },
            'containers': [
                {
                    'name': 'pipelines-persistence',
                    'args': [
                        'persistence_agent',
                        '--alsologtostderr=true',
                        f'--mlPipelineAPIServerName={api}',
                        f'--namespace={os.environ["JUJU_MODEL_NAME"]}',
                    ],
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'config': {'POD_NAMESPACE': os.environ['JUJU_MODEL_NAME']},
                }
            ],
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
