import os

from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import set_flag, clear_flag, when, when_not, endpoint_from_name


@when('charm.started')
def charm_ready():
    layer.status.active('')


@when('layer.docker-resource.oci-image.changed', 'config.changed')
def update_image():
    clear_flag('charm.started')


@when_not('endpoint.redis.available')
def blocked():
    goal_state = hookenv.goal_state()
    if 'redis' in goal_state['relations']:
        layer.status.waiting('waiting for redis')
    else:
        layer.status.blocked('missing relation to redis')
    clear_flag('charm.started')


@when('layer.docker-resource.oci-image.available', 'endpoint.redis.available')
@when_not('charm.started')
def start_charm():
    layer.status.maintenance('configuring container')

    config = hookenv.config()
    image_info = layer.docker_resource.get_info('oci-image')
    model = os.environ['JUJU_MODEL_NAME']
    redis = endpoint_from_name('redis')

    layer.caas_base.pod_spec_set(
        {
            'containers': [
                {
                    'name': 'seldon-cluster-manager',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'ports': [{'name': 'cluster-manager', 'containerPort': config['port']}],
                    'config': {
                        'ENGINE_CONTAINER_IMAGE_AND_VERSION': config['engine-image'],
                        'ENGINE_CONTAINER_IMAGE_PULL_POLICY': 'IfNotPresent',
                        'ENGINE_CONTAINER_SERVICE_ACCOUNT_NAME': 'default',
                        'ENGINE_CONTAINER_USER': '8888',
                        'ENGINE_SERVER_GRPC_PORT': '5001',
                        'ENGINE_SERVER_PORT': '8000',
                        'JAVA_OPTS': config['java-opts'],
                        'PREDICTIVE_UNIT_SERVICE_PORT': '8501',
                        'SELDON_CLUSTER_MANAGER_POD_NAMESPACE': model,
                        'SELDON_CLUSTER_MANAGER_REDIS_HOST': redis.all_joined_units[
                            0
                        ].application_name,
                        'SELDON_CLUSTER_MANAGER_SINGLE_NAMESPACE': True,
                        'SPRING_OPTS': config['spring-opts'],
                    },
                }
            ]
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
