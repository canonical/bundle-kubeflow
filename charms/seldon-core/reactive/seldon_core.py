import os
import shutil
from base64 import b64encode
from pathlib import Path
from subprocess import run

import yaml

from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import clear_flag, hook, set_flag, when, when_any, when_not


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

    ca_bundle = b64encode(Path('cert.pem').read_bytes()).decode('utf-8')

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
            'serviceAccount': {
                'global': True,
                'rules': [
                    {
                        'apiGroups': [''],
                        'resources': ['namespaces'],
                        'verbs': ['get', 'list', 'watch'],
                    },
                    {
                        'apiGroups': [''],
                        'resources': ['services'],
                        'verbs': ['create', 'delete', 'get', 'list', 'patch', 'update', 'watch'],
                    },
                    {
                        'apiGroups': ['apps'],
                        'resources': ['deployments'],
                        'verbs': ['create', 'delete', 'get', 'list', 'patch', 'update', 'watch'],
                    },
                    {
                        'apiGroups': ['apps'],
                        'resources': ['deployments/status'],
                        'verbs': ['get', 'patch', 'update'],
                    },
                    {
                        'apiGroups': ['autoscaling'],
                        'resources': ['horizontalpodautoscalers'],
                        'verbs': ['create', 'delete', 'get', 'list', 'patch', 'update', 'watch'],
                    },
                    {
                        'apiGroups': ['autoscaling'],
                        'resources': ['horizontalpodautoscalers/status'],
                        'verbs': ['get', 'patch', 'update'],
                    },
                    {
                        'apiGroups': ['machinelearning.seldon.io'],
                        'resources': ['seldondeployments'],
                        'verbs': ['create', 'delete', 'get', 'list', 'patch', 'update', 'watch'],
                    },
                    {
                        'apiGroups': ['machinelearning.seldon.io'],
                        'resources': ['seldondeployments/finalizers'],
                        'verbs': ['get', 'patch', 'update'],
                    },
                    {
                        'apiGroups': ['machinelearning.seldon.io'],
                        'resources': ['seldondeployments/status'],
                        'verbs': ['get', 'patch', 'update'],
                    },
                    {
                        'apiGroups': ['networking.istio.io'],
                        'resources': ['destinationrules'],
                        'verbs': ['create', 'delete', 'get', 'list', 'patch', 'update', 'watch'],
                    },
                    {
                        'apiGroups': ['networking.istio.io'],
                        'resources': ['destinationrules/status'],
                        'verbs': ['get', 'patch', 'update'],
                    },
                    {
                        'apiGroups': ['networking.istio.io'],
                        'resources': ['virtualservices'],
                        'verbs': ['create', 'delete', 'get', 'list', 'patch', 'update', 'watch'],
                    },
                    {
                        'apiGroups': ['networking.istio.io'],
                        'resources': ['virtualservices/status'],
                        'verbs': ['get', 'patch', 'update'],
                    },
                    {
                        'apiGroups': ['v1'],
                        'resources': ['namespaces'],
                        'verbs': ['get', 'list', 'watch'],
                    },
                    {
                        'apiGroups': ['v1'],
                        'resources': ['services'],
                        'verbs': ['create', 'delete', 'get', 'list', 'patch', 'update', 'watch'],
                    },
                    {
                        'apiGroups': ['v1'],
                        'resources': ['services/status'],
                        'verbs': ['get', 'patch', 'update'],
                    },
                ],
            },
            'containers': [
                {
                    'name': 'seldon-core',
                    'command': ['/manager'],
                    'args': [
                        '--enable-leader-election',
                        '--webhook-port',
                        str(config['webhook-port']),
                    ],
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
                        'CONTROLLER_NAME': '',
                        'AMBASSADOR_ENABLED': 'true',
                        'AMBASSADOR_SINGLE_NAMESPACE': 'false',
                        'ENGINE_CONTAINER_IMAGE_AND_VERSION': 'docker.io/seldonio/engine:1.0.1',
                        'ENGINE_CONTAINER_IMAGE_PULL_POLICY': 'IfNotPresent',
                        'ENGINE_CONTAINER_SERVICE_ACCOUNT_NAME': 'default',
                        'ENGINE_CONTAINER_USER': '8888',
                        'ENGINE_LOG_MESSAGES_EXTERNALLY': 'false',
                        'PREDICTIVE_UNIT_SERVICE_PORT': '9000',
                        'ENGINE_SERVER_GRPC_PORT': '5001',
                        'ENGINE_SERVER_PORT': '8000',
                        'ENGINE_PROMETHEUS_PATH': 'prometheus',
                        'ISTIO_ENABLED': 'false',
                        'ISTIO_GATEWAY': 'kubeflow-gateway',
                        'ISTIO_TLS_MODE': '',
                    },
                    'files': [
                        {
                            'name': 'certs',
                            'mountPath': '/tmp/k8s-webhook-server/serving-certs',
                            'files': {
                                'tls.crt': Path('cert.pem').read_text(),
                                'tls.key': Path('key.pem').read_text(),
                            },
                        }
                    ],
                }
            ],
        },
        k8s_resources={
            'kubernetesResources': {
                'customResourceDefinitions': {
                    crd['metadata']['name']: crd['spec']
                    for crd in yaml.safe_load_all(Path("files/crds.yaml").read_text())
                },
                'mutatingWebhookConfigurations': {
                    'seldon-mutating-webhook-configuration-kubeflow': [
                        {
                            'name': 'mseldondeployment.kb.io',
                            'failurePolicy': 'Fail',
                            'clientConfig': {
                                'caBundle': ca_bundle,
                                'service': {
                                    'name': hookenv.service_name(),
                                    'namespace': model,
                                    'path': '/mutate-machinelearning-seldon-io-v1-seldondeployment',
                                },
                            },
                            'namespaceSelector': {
                                'matchExpressions': [
                                    {'key': 'seldon.io/controller-id', 'operator': 'DoesNotExist'}
                                ],
                                'matchLabels': {'serving.kubeflow.org/inferenceservice': 'enabled'},
                            },
                            'rules': [
                                {
                                    'apiGroups': ['machinelearning.seldon.io'],
                                    'apiVersions': ['v1'],
                                    'operations': ['CREATE', 'UPDATE'],
                                    'resources': ['seldondeployments'],
                                }
                            ],
                        },
                        {
                            'clientConfig': {
                                'caBundle': ca_bundle,
                                'service': {
                                    'name': hookenv.service_name(),
                                    'namespace': model,
                                    'path': '/mutate-machinelearning-seldon-io-v1alpha2-seldondeployment',
                                },
                            },
                            'failurePolicy': 'Fail',
                            'name': 'mseldondeployment.kb.io',
                            'namespaceSelector': {
                                'matchExpressions': [
                                    {'key': 'seldon.io/controller-id', 'operator': 'DoesNotExist'}
                                ],
                                'matchLabels': {'serving.kubeflow.org/inferenceservice': 'enabled'},
                            },
                            'rules': [
                                {
                                    'apiGroups': ['machinelearning.seldon.io'],
                                    'apiVersions': ['v1alpha2'],
                                    'operations': ['CREATE', 'UPDATE'],
                                    'resources': ['seldondeployments'],
                                }
                            ],
                        },
                        {
                            'clientConfig': {
                                'caBundle': ca_bundle,
                                'service': {
                                    'name': hookenv.service_name(),
                                    'namespace': model,
                                    'path': '/mutate-machinelearning-seldon-io-v1alpha3-seldondeployment',
                                },
                            },
                            'failurePolicy': 'Fail',
                            'name': 'mseldondeployment.kb.io',
                            'namespaceSelector': {
                                'matchExpressions': [
                                    {'key': 'seldon.io/controller-id', 'operator': 'DoesNotExist'}
                                ],
                                'matchLabels': {'serving.kubeflow.org/inferenceservice': 'enabled'},
                            },
                            'rules': [
                                {
                                    'apiGroups': ['machinelearning.seldon.io'],
                                    'apiVersions': ['v1alpha3'],
                                    'operations': ['CREATE', 'UPDATE'],
                                    'resources': ['seldondeployments'],
                                }
                            ],
                        },
                    ]
                },
                #  'validatingWebhookConfigurations': {
                #      'seldon-validating-webhook-configuration-kubeflow': [
                #          {
                #              'clientConfig': {
                #                  'caBundle': ca_bundle,
                #                  'service': {
                #                      'name': hookenv.service_name(),
                #                      'namespace': model,
                #                      'path': '/validate-machinelearning-seldon-io-v1-seldondeployment',
                #                  },
                #              },
                #              'failurePolicy': 'Fail',
                #              'name': 'vseldondeployment.kb.io',
                #              'namespaceSelector': {
                #                  'matchExpressions': [
                #                      {'key': 'seldon.io/controller-id', 'operator': 'DoesNotExist'}
                #                  ],
                #                  'matchLabels': {'serving.kubeflow.org/inferenceservice': 'enabled'},
                #              },
                #              'rules': [
                #                  {
                #                      'apiGroups': ['machinelearning.seldon.io'],
                #                      'apiVersions': ['v1'],
                #                      'operations': ['CREATE', 'UPDATE'],
                #                      'resources': ['seldondeployments'],
                #                  }
                #              ],
                #          },
                #          {
                #              'clientConfig': {
                #                  'caBundle': ca_bundle,
                #                  'service': {
                #                      'name': hookenv.service_name(),
                #                      'namespace': model,
                #                      'path': '/validate-machinelearning-seldon-io-v1alpha2-seldondeployment',
                #                  },
                #              },
                #              'failurePolicy': 'Fail',
                #              'name': 'vseldondeployment.kb.io',
                #              'namespaceSelector': {
                #                  'matchExpressions': [
                #                      {'key': 'seldon.io/controller-id', 'operator': 'DoesNotExist'}
                #                  ],
                #                  'matchLabels': {'serving.kubeflow.org/inferenceservice': 'enabled'},
                #              },
                #              'rules': [
                #                  {
                #                      'apiGroups': ['machinelearning.seldon.io'],
                #                      'apiVersions': ['v1alpha2'],
                #                      'operations': ['CREATE', 'UPDATE'],
                #                      'resources': ['seldondeployments'],
                #                  }
                #              ],
                #          },
                #          {
                #              'clientConfig': {
                #                  'caBundle': ca_bundle,
                #                  'service': {
                #                      'name': hookenv.service_name(),
                #                      'namespace': model,
                #                      'path': '/validate-machinelearning-seldon-io-v1alpha3-seldondeployment',
                #                  },
                #              },
                #              'failurePolicy': 'Fail',
                #              'name': 'vseldondeployment.kb.io',
                #              'namespaceSelector': {
                #                  'matchExpressions': [
                #                      {'key': 'seldon.io/controller-id', 'operator': 'DoesNotExist'}
                #                  ],
                #                  'matchLabels': {'serving.kubeflow.org/inferenceservice': 'enabled'},
                #              },
                #              'rules': [
                #                  {
                #                      'apiGroups': ['machinelearning.seldon.io'],
                #                      'apiVersions': ['v1alpha3'],
                #                      'operations': ['CREATE', 'UPDATE'],
                #                      'resources': ['seldondeployments'],
                #                  }
                #              ],
                #          },
                #      ]
                #  },
            }
        },
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
