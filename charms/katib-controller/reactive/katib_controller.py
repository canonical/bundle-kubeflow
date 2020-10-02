import json
import os
from pathlib import Path
from subprocess import check_call
from base64 import b64encode

import yaml

from charmhelpers.core import hookenv
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


KATIB_CONFIG = {
    'metrics-collector-sidecar': json.dumps(
        {
            "StdOut": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/file-metrics-collector:v0.9.0"
            },
            "File": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/file-metrics-collector:v0.9.0"
            },
            "TensorFlowEvent": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/tfevent-metrics-collector:v0.9.0"
            },
        }
    ),
    'suggestion': json.dumps(
        {
            "random": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/suggestion-hyperopt:v0.9.0"
            },
            "grid": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/suggestion-chocolate:v0.9.0"
            },
            "hyperband": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/suggestion-hyperband:v0.9.0"
            },
            "bayesianoptimization": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/suggestion-skopt:v0.9.0"
            },
            "tpe": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/suggestion-hyperopt:v0.9.0"
            },
            "nasrl": {
                "image": "gcr.io/kubeflow-images-public/katib/v1alpha3/suggestion-nasrl:v0.9.0"
            },
        }
    ),
}


def gen_certs(namespace, service_name):
    if Path('/run/cert.pem').exists():
        hookenv.log("Found existing cert.pem, not generating new cert.")
        return

    Path('/run/ssl.conf').write_text(
        f"""[ req ]
default_bits = 2048
prompt = no
default_md = sha256
req_extensions = req_ext
distinguished_name = dn

[ dn ]
C = GB
ST = Canonical
L = Canonical
O = Canonical
OU = Canonical
CN = 127.0.0.1

[ req_ext ]
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = {service_name}
DNS.2 = {service_name}.{namespace}
DNS.3 = {service_name}.{namespace}.svc
DNS.4 = {service_name}.{namespace}.svc.cluster
DNS.5 = {service_name}.{namespace}.svc.cluster.local
IP.1 = 127.0.0.1

[ v3_ext ]
authorityKeyIdentifier=keyid,issuer:always
basicConstraints=CA:FALSE
keyUsage=keyEncipherment,dataEncipherment,digitalSignature
extendedKeyUsage=serverAuth,clientAuth
subjectAltName=@alt_names"""
    )

    check_call(['openssl', 'genrsa', '-out', '/run/ca.key', '2048'])
    check_call(['openssl', 'genrsa', '-out', '/run/server.key', '2048'])
    check_call(
        [
            'openssl',
            'req',
            '-x509',
            '-new',
            '-sha256',
            '-nodes',
            '-days',
            '3650',
            '-key',
            '/run/ca.key',
            '-subj',
            '/CN=127.0.0.1',
            '-out',
            '/run/ca.crt',
        ]
    )
    check_call(
        [
            'openssl',
            'req',
            '-new',
            '-sha256',
            '-key',
            '/run/server.key',
            '-out',
            '/run/server.csr',
            '-config',
            '/run/ssl.conf',
        ]
    )
    check_call(
        [
            'openssl',
            'x509',
            '-req',
            '-sha256',
            '-in',
            '/run/server.csr',
            '-CA',
            '/run/ca.crt',
            '-CAkey',
            '/run/ca.key',
            '-CAcreateserial',
            '-out',
            '/run/cert.pem',
            '-days',
            '365',
            '-extensions',
            'v3_ext',
            '-extfile',
            '/run/ssl.conf',
        ]
    )


@when('layer.docker-resource.oci-image.available')
@when_not('charm.started')
def start_charm():
    if not hookenv.is_leader():
        hookenv.log("This unit is not a leader.")
        return False

    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')
    namespace = os.environ["JUJU_MODEL_NAME"]
    config = dict(hookenv.config())

    gen_certs(namespace, hookenv.service_name())
    ca_bundle = b64encode(Path('/run/cert.pem').read_bytes()).decode('utf-8')

    layer.caas_base.pod_spec_set(
        {
            'version': 3,
            'serviceAccount': {
                'roles': [
                    {
                        'rules': [
                            {
                                'apiGroups': [''],
                                'resources': [
                                    'configmaps',
                                    'serviceaccounts',
                                    'services',
                                    'secrets',
                                    'events',
                                    'namespaces',
                                ],
                                'verbs': ['*'],
                            },
                            {
                                'apiGroups': [''],
                                'resources': ['pods', 'pods/log', 'pods/status'],
                                'verbs': ['*'],
                            },
                            {'apiGroups': ['apps'], 'resources': ['deployments'], 'verbs': ['*']},
                            {
                                'apiGroups': ['batch'],
                                'resources': ['jobs', 'cronjobs'],
                                'verbs': ['*'],
                            },
                            {
                                'apiGroups': ['apiextensions.k8s.io'],
                                'resources': ['customresourcedefinitions'],
                                'verbs': ['create', 'get'],
                            },
                            {
                                'apiGroups': ['admissionregistration.k8s.io'],
                                'resources': [
                                    'validatingwebhookconfigurations',
                                    'mutatingwebhookconfigurations',
                                ],
                                'verbs': ['*'],
                            },
                            {
                                'apiGroups': ['kubeflow.org'],
                                'resources': [
                                    'experiments',
                                    'experiments/status',
                                    'trials',
                                    'trials/status',
                                    'suggestions',
                                    'suggestions/status',
                                ],
                                'verbs': ['*'],
                            },
                            {
                                'apiGroups': ['kubeflow.org'],
                                'resources': ['tfjobs', 'pytorchjobs'],
                                'verbs': ['*'],
                            },
                        ]
                    }
                ]
            },
            'containers': [
                {
                    'name': 'katib-controller',
                    'command': ["./katib-controller"],
                    'args': [
                        '-webhook-port',
                        str(config['webhook-port']),
                        '-logtostderr',
                        '-webhook-service-name',
                        'katib-controller-old',
                        '-v=4',
                    ],
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'ports': [
                        {'name': 'webhook', 'containerPort': config['webhook-port']},
                        {'name': 'metrics', 'containerPort': config['metrics-port']},
                    ],
                    'envConfig': {'KATIB_CORE_NAMESPACE': os.environ['JUJU_MODEL_NAME']},
                    'volumeConfig': [
                        {
                            'name': 'cert',
                            'mountPath': '/tmp/cert',
                            'files': [
                                {'path': 'cert.pem', 'content': Path('/run/cert.pem').read_text()},
                                {'path': 'key.pem', 'content': Path('/run/server.key').read_text()},
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
                "mutatingWebhookConfigurations": [
                    {
                        "name": "katib-mutating-webhook-config",
                        "webhooks": [
                            {
                                "name": "mutating.experiment.katib.kubeflow.org",
                                "rules": [
                                    {
                                        'apiGroups': ['kubeflow.org'],
                                        'apiVersions': ['v1alpha3'],
                                        'operations': ['CREATE', 'UPDATE'],
                                        'resources': ['experiments'],
                                        'scope': '*',
                                    }
                                ],
                                "failurePolicy": "Fail",
                                "clientConfig": {
                                    "service": {
                                        "name": hookenv.service_name(),
                                        "namespace": namespace,
                                        "path": "/mutate-experiments",
                                        "port": config['webhook-port'],
                                    },
                                    "caBundle": ca_bundle,
                                },
                            },
                            {
                                "name": "mutating.pod.katib.kubeflow.org",
                                "rules": [
                                    {
                                        'apiGroups': [''],
                                        'apiVersions': ['v1'],
                                        'operations': ['CREATE'],
                                        'resources': ['pods'],
                                        'scope': '*',
                                    }
                                ],
                                "failurePolicy": "Ignore",
                                "clientConfig": {
                                    "service": {
                                        "name": hookenv.service_name(),
                                        "namespace": namespace,
                                        "path": "/mutate-pods",
                                        "port": config['webhook-port'],
                                    },
                                    "caBundle": ca_bundle,
                                },
                            },
                        ],
                    }
                ],
                "validatingWebhookConfigurations": [
                    {
                        "name": "katib-validating-webhook-config",
                        "webhooks": [
                            {
                                "name": "validating.experiment.katib.kubeflow.org",
                                "rules": [
                                    {
                                        "apiGroups": ["kubeflow.org"],
                                        "apiVersions": ["v1alpha3"],
                                        "operations": ["CREATE", "UPDATE"],
                                        "resources": ["experiments"],
                                        'scope': '*',
                                    }
                                ],
                                "failurePolicy": "Fail",
                                "sideEffects": "Unknown",
                                "clientConfig": {
                                    "service": {
                                        "name": hookenv.service_name(),
                                        "namespace": namespace,
                                        "path": "/validate-experiments",
                                        "port": config['webhook-port'],
                                    },
                                    "caBundle": ca_bundle,
                                },
                            }
                        ],
                    }
                ],
            },
            'configMaps': {
                'katib-config': KATIB_CONFIG,
                'trial-template': {
                    'defaultTrialTemplate.yaml': Path(
                        'files/defaultTrialTemplate.yaml.tmpl'
                    ).read_text()
                },
            },
        },
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
