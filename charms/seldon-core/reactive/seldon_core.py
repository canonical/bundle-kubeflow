import os
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


@when_any(
    'layer.docker-resource.oci-image.changed', 'config.changed', 'endpoint.service-mesh.joined'
)
def update_image():
    clear_flag('charm.started')


@hook('service-mesh-relation-broken')
def service_mesh_unjoined(_):
    clear_flag('charm.started')


@when('layer.docker-resource.oci-image.available')
@when_not('charm.started')
def start_charm():
    if not hookenv.is_leader():
        hookenv.log("This unit is not a leader.")
        return False

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

    envs = {
        'AMBASSADOR_ENABLED': config['ambassador-enabled'],
        'AMBASSADOR_SINGLE_NAMESPACE': config['ambassador-single-namespace'],
        'CONTROLLER_ID': config['controller-id'],
        'DEFAULT_USER_ID': config['default-user-id'],
        'ENGINE_CONTAINER_IMAGE_AND_VERSION': config['engine-container-image-and-version'],
        'ENGINE_CONTAINER_IMAGE_PULL_POLICY': config['engine-container-image-pull-policy'],
        'ENGINE_CONTAINER_SERVICE_ACCOUNT_NAME': config['engine-container-service-account-name'],
        'ENGINE_CONTAINER_USER': config['engine-container-user'],
        'ENGINE_LOG_MESSAGES_EXTERNALLY': config['engine-log-messages-externally'],
        'ENGINE_PROMETHEUS_PATH': config['engine-prometheus-path'],
        'ENGINE_SERVER_GRPC_PORT': config['engine-server-grpc-port'],
        'ENGINE_SERVER_PORT': config['engine-server-port'],
        'EXECUTOR_CONTAINER_IMAGE_AND_VERSION': config['executor-container-image-and-version'],
        'EXECUTOR_CONTAINER_IMAGE_PULL_POLICY': config['executor-container-image-pull-policy'],
        'EXECUTOR_CONTAINER_SERVICE_ACCOUNT_NAME': config[
            'executor-container-service-account-name'
        ],
        'EXECUTOR_CONTAINER_USER': config['executor-container-user'],
        'EXECUTOR_PROMETHEUS_PATH': config['executor-prometheus-path'],
        'EXECUTOR_REQUEST_LOGGER_DEFAULT_ENDPOINT': config[
            'executor-request-logger-default-endpoint'
        ],
        'EXECUTOR_SERVER_METRICS_PORT_NAME': config['executor-server-metrics-port-name'],
        'EXECUTOR_SERVER_PORT': config['executor-server-port'],
        'ISTIO_ENABLED': hookenv.is_relation_made('service-mesh'),
        'ISTIO_GATEWAY': config['istio-gateway'],
        'ISTIO_TLS_MODE': config['istio-tls-mode'],
        'MANAGER_CREATE_RESOURCES': config['manager-create-resources'],
        'POD_NAMESPACE': model,
        'PREDICTIVE_UNIT_DEFAULT_ENV_SECRET_REF_NAME': config[
            'predictive-unit-default-env-secret-ref-name'
        ],
        'PREDICTIVE_UNIT_METRICS_PORT_NAME': config['predictive-unit-metrics-port-name'],
        'PREDICTIVE_UNIT_SERVICE_PORT': config['predictive-unit-service-port'],
        'RELATED_IMAGE_ENGINE': config['related-image-engine'],
        'RELATED_IMAGE_EXECUTOR': config['related-image-executor'],
        'RELATED_IMAGE_EXPLAINER': config['related-image-explainer'],
        'RELATED_IMAGE_MLFLOWSERVER_GRPC': config['related-image-mlflowserver-grpc'],
        'RELATED_IMAGE_MLFLOWSERVER_REST': config['related-image-mlflowserver-rest'],
        'RELATED_IMAGE_SKLEARNSERVER_GRPC': config['related-image-sklearnserver-grpc'],
        'RELATED_IMAGE_SKLEARNSERVER_REST': config['related-image-sklearnserver-rest'],
        'RELATED_IMAGE_STORAGE_INITIALIZER': config['related-image-storage-initializer'],
        'RELATED_IMAGE_TENSORFLOW': config['related-image-tensorflow'],
        'RELATED_IMAGE_TFPROXY_GRPC': config['related-image-tfproxy-grpc'],
        'RELATED_IMAGE_TFPROXY_REST': config['related-image-tfproxy-rest'],
        'RELATED_IMAGE_XGBOOSTSERVER_GRPC': config['related-image-xgboostserver-grpc'],
        'RELATED_IMAGE_XGBOOSTSERVER_REST': config['related-image-xgboostserver-rest'],
        'USE_EXECUTOR': config['use-executor'],
        'WATCH_NAMESPACE': config['watch-namespace'],
    }

    layer.caas_base.pod_spec_set(
        {
            'version': 3,
            'serviceAccount': {
                'roles': [
                    {
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
                                'verbs': [
                                    'create',
                                    'delete',
                                    'get',
                                    'list',
                                    'patch',
                                    'update',
                                    'watch',
                                ],
                            },
                            {
                                'apiGroups': ['apps'],
                                'resources': ['deployments'],
                                'verbs': [
                                    'create',
                                    'delete',
                                    'get',
                                    'list',
                                    'patch',
                                    'update',
                                    'watch',
                                ],
                            },
                            {
                                'apiGroups': ['apps'],
                                'resources': ['deployments/status'],
                                'verbs': ['get', 'patch', 'update'],
                            },
                            {
                                'apiGroups': ['autoscaling'],
                                'resources': ['horizontalpodautoscalers'],
                                'verbs': [
                                    'create',
                                    'delete',
                                    'get',
                                    'list',
                                    'patch',
                                    'update',
                                    'watch',
                                ],
                            },
                            {
                                'apiGroups': ['autoscaling'],
                                'resources': ['horizontalpodautoscalers/status'],
                                'verbs': ['get', 'patch', 'update'],
                            },
                            {
                                'apiGroups': ['machinelearning.seldon.io'],
                                'resources': ['seldondeployments'],
                                'verbs': [
                                    'create',
                                    'delete',
                                    'get',
                                    'list',
                                    'patch',
                                    'update',
                                    'watch',
                                ],
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
                                'verbs': [
                                    'create',
                                    'delete',
                                    'get',
                                    'list',
                                    'patch',
                                    'update',
                                    'watch',
                                ],
                            },
                            {
                                'apiGroups': ['networking.istio.io'],
                                'resources': ['destinationrules/status'],
                                'verbs': ['get', 'patch', 'update'],
                            },
                            {
                                'apiGroups': ['networking.istio.io'],
                                'resources': ['virtualservices'],
                                'verbs': [
                                    'create',
                                    'delete',
                                    'get',
                                    'list',
                                    'patch',
                                    'update',
                                    'watch',
                                ],
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
                                'verbs': [
                                    'create',
                                    'delete',
                                    'get',
                                    'list',
                                    'patch',
                                    'update',
                                    'watch',
                                ],
                            },
                            {
                                'apiGroups': ['v1'],
                                'resources': ['services/status'],
                                'verbs': ['get', 'patch', 'update'],
                            },
                        ],
                    }
                ]
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
                    'envConfig': envs,
                    'volumeConfig': [
                        {
                            'name': 'certs',
                            'mountPath': '/tmp/k8s-webhook-server/serving-certs',
                            'files': [
                                {'path': 'tls.crt', 'content': Path('cert.pem').read_text()},
                                {'path': 'tls.key', 'content': Path('key.pem').read_text()},
                            ],
                        }
                    ],
                }
            ],
        },
        k8s_resources={
            'kubernetesResources': {
                'customResourceDefinitions': [
                    {'name': crd['metadata']['name'], 'spec': crd['spec']}
                    for crd in yaml.safe_load_all(Path("files/crds.yaml").read_text())
                ],
                'mutatingWebhookConfigurations': [
                    {
                        'name': 'seldon-mutating-webhook-configuration-kubeflow',
                        'webhooks': [
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
                                        {
                                            'key': 'seldon.io/controller-id',
                                            'operator': 'DoesNotExist',
                                        }
                                    ],
                                    'matchLabels': {
                                        'serving.kubeflow.org/inferenceservice': 'enabled'
                                    },
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
                                        {
                                            'key': 'seldon.io/controller-id',
                                            'operator': 'DoesNotExist',
                                        }
                                    ],
                                    'matchLabels': {
                                        'serving.kubeflow.org/inferenceservice': 'enabled'
                                    },
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
                                        {
                                            'key': 'seldon.io/controller-id',
                                            'operator': 'DoesNotExist',
                                        }
                                    ],
                                    'matchLabels': {
                                        'serving.kubeflow.org/inferenceservice': 'enabled'
                                    },
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
                        ],
                    }
                ],
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
