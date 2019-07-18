import os
from pathlib import Path
from subprocess import run

import yaml

from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import clear_flag, set_flag, when, when_not, when_any


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

    config = hookenv.config()
    image_info = layer.docker_resource.get_info('oci-image')
    model = os.environ['JUJU_MODEL_NAME']
    crd = yaml.safe_load(Path("files/crd-v1alpha2.yaml").read_text())

    run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:4096",
            "-keyout",
            "key.pem",
            "-out",
            "cert.pem",
            "-days",
            "365",
            "-subj",
            f"/CN={hookenv.service_name()}.{model}.svc",
            "-nodes",
        ],
        check=True,
    )

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
            'serviceAccount': {
                'global': True,
                'rules': [
                    {
                        'apiGroups': ['apps'],
                        'resources': ['deployments'],
                        'verbs': ['get', 'list', 'watch', 'create', 'update', 'patch', 'delete'],
                    },
                    {
                        'apiGroups': ['apps'],
                        'resources': ['deployments/status'],
                        'verbs': ['get', 'update', 'patch'],
                    },
                    {
                        'apiGroups': ['v1'],
                        'resources': ['services'],
                        'verbs': ['get', 'list', 'watch', 'create', 'update', 'patch', 'delete'],
                    },
                    {
                        'apiGroups': ['v1'],
                        'resources': ['services/status'],
                        'verbs': ['get', 'update', 'patch'],
                    },
                    {
                        'apiGroups': ['networking.istio.io'],
                        'resources': ['virtualservices'],
                        'verbs': ['get', 'list', 'watch', 'create', 'update', 'patch', 'delete'],
                    },
                    {
                        'apiGroups': ['networking.istio.io'],
                        'resources': ['virtualservices/status'],
                        'verbs': ['get', 'update', 'patch'],
                    },
                    {
                        'apiGroups': ['networking.istio.io'],
                        'resources': ['destinationrules'],
                        'verbs': ['get', 'list', 'watch', 'create', 'update', 'patch', 'delete'],
                    },
                    {
                        'apiGroups': ['networking.istio.io'],
                        'resources': ['destinationrules/status'],
                        'verbs': ['get', 'update', 'patch'],
                    },
                    {
                        'apiGroups': ['autoscaling'],
                        'resources': ['horizontalpodautoscalers'],
                        'verbs': ['get', 'list', 'watch', 'create', 'update', 'patch', 'delete'],
                    },
                    {
                        'apiGroups': ['autoscaling'],
                        'resources': ['horizontalpodautoscalers/status'],
                        'verbs': ['get', 'update', 'patch'],
                    },
                    {
                        'apiGroups': ['machinelearning.seldon.io'],
                        'resources': ['seldondeployments'],
                        'verbs': ['get', 'list', 'watch', 'create', 'update', 'patch', 'delete'],
                    },
                    {
                        'apiGroups': ['machinelearning.seldon.io'],
                        'resources': ['seldondeployments/status'],
                        'verbs': ['get', 'update', 'patch'],
                    },
                    {
                        'apiGroups': ['admissionregistration.k8s.io'],
                        'resources': [
                            'mutatingwebhookconfigurations',
                            'validatingwebhookconfigurations',
                        ],
                        'verbs': ['get', 'list', 'watch', 'create', 'update', 'patch', 'delete'],
                    },
                    {
                        'apiGroups': [''],
                        'resources': ['secrets'],
                        'verbs': ['get', 'list', 'watch', 'create', 'update', 'patch', 'delete'],
                    },
                    {
                        'apiGroups': [''],
                        'resources': ['services'],
                        'verbs': ['get', 'list', 'watch', 'create', 'update', 'patch', 'delete'],
                    },
                ],
            },
            'containers': [
                {
                    'name': 'seldon-core',
                    'command': ['/manager'],
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'ports': [
                        {'name': 'metrics', 'containerPort': config['metrics-port']},
                        {'name': 'webhook', 'containerPort': config['webhook-port']},
                    ],
                    'config': {
                        'POD_NAMESPACE': model,
                        'SECRET_NAME': 'seldon-operator-webhook-server-secret',
                        'AMBASSADOR_ENABLED': 'true',
                        'AMBASSADOR_SINGLE_NAMESPACE': 'false',
                        'ENGINE_CONTAINER_IMAGE_AND_VERSION': 'docker.io/seldonio/engine:0.4.1',
                        'ENGINE_CONTAINER_IMAGE_PULL_POLICY': 'IfNotPresent',
                        'ENGINE_CONTAINER_SERVICE_ACCOUNT_NAME': 'default',
                        'ENGINE_CONTAINER_USER': '8888',
                        'PREDICTIVE_UNIT_SERVICE_PORT': '9000',
                        'ENGINE_SERVER_GRPC_PORT': '5001',
                        'ENGINE_SERVER_PORT': '8000',
                        'ENGINE_PROMETHEUS_PATH': 'prometheus',
                        'ISTIO_ENABLED': 'false',
                        'ISTIO_GATEWAY': 'kubeflow-gateway',
                    },
                    'files': [
                        {
                            'name': 'cert',
                            'mountPath': '/tmp/cert',
                            'files': {
                                'cert.pem': Path('cert.pem').read_text(),
                                'key.pem': Path('key.pem').read_text(),
                            },
                        }
                    ],
                }
            ],
        },
        k8s_resources={
            'kubernetesResources': {
                'customResourceDefinitions': {crd['metadata']['name']: crd['spec']}
            }
        },
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
