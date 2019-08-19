import os
from pathlib import Path

import yaml
from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import set_flag, clear_flag, when, when_not


@when('charm.started')
def charm_ready():
    layer.status.active('')


@when('layer.docker-resource.oci-image.changed', 'config.changed')
def update_image():
    clear_flag('charm.started')


@when('layer.docker-resource.oci-image.available')
@when_not('charm.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    crd = yaml.safe_load(Path('files/crd-v1beta2.yaml').read_text())
    config = yaml.dump(
        {'grpcServerFilePath': '/opt/mlkube/grpc_tensorflow_server/grpc_tensorflow_server.py'}
    )

    layer.caas_base.pod_spec_set(
        {
            'omitServiceFrontend': True,
            'containers': [
                {
                    'name': 'tf-job-operator',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'command': [
                        '/opt/kubeflow/tf-operator.v1',
                        '--alsologtostderr',
                        '-v=1',
                        '--monitoring-port=8443',
                    ],
                    'serviceAccountName': 'tf-job-operator',
                    'config': {
                        'MY_POD_NAMESPACE': os.environ['JUJU_MODEL_NAME'],
                        'MY_POD_NAME': hookenv.service_name(),
                    },
                    'files': [
                        {
                            'name': 'configs',
                            'mountPath': '/etc/config',
                            'files': {'controller_config_file.yaml': config},
                        }
                    ],
                }
            ],
            'customResourceDefinitions': {crd['metadata']['name']: crd['spec']},
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
