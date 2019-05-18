from charms import layer
from charms.reactive import set_flag, clear_flag, when, when_not


@when('charm.pipelines-persistence.started')
def charm_ready():
    layer.status.active('')


@when('layer.docker-resource.oci-image.changed')
def update_image():
    clear_flag('charm.pipelines-persistence.started')


@when('layer.docker-resource.oci-image.available')
@when_not('charm.pipelines-persistence.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    layer.caas_base.pod_spec_set(
        {
            'containers': [
                {
                    'name': 'pipelines-persistence',
                    'args': [
                        'persistence_agent',
                        '--alsologtostderr=true',
                        '--mlPipelineAPIServerName=pipelines-api',
                        '--namespace=kubeflow',
                    ],
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'ports': [{'name': 'dummy', 'containerPort': 9999}],
                }
            ]
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.pipelines-persistence.started')
