import os
from base64 import b64decode
from pathlib import Path
from subprocess import run

from kubernetes import client, config
from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import clear_flag, hook, set_flag, when, when_any, when_not


@hook("upgrade-charm")
def upgrade_charm():
    clear_flag("charm.started")


@when("charm.started")
def charm_ready():
    layer.status.active("")


@when('cert-manager-webhook.available')
def configure_http(http):
    http.configure(port=hookenv.config('port'), hostname=hookenv.application_name())


@when_any("layer.docker-resource.oci-image.changed", "config.changed")
def update_image():
    clear_flag("charm.started")


@when("layer.docker-resource.oci-image.available")
@when_not("charm.started")
def start_charm():
    layer.status.maintenance("configuring container")

    image_info = layer.docker_resource.get_info("oci-image")

    namespace = os.environ["JUJU_MODEL_NAME"]
    port = hookenv.config("port")

    # Talk to the K8s API to read the auto-generated webhook certificate secret.
    # Borrow the env vars from the root process that let the Kubernetes
    # client automatically look up connection info, since `load_incluster_config`
    # for whatever reason doesn't support loading the serviceaccount token from disk.
    os.environ.update(
        dict(
            e.split("=")
            for e in Path("/proc/1/environ").read_text().split("\x00")
            if "KUBERNETES_SERVICE" in e
        )
    )

    config.load_incluster_config()
    v1 = client.CoreV1Api()
    try:
        secret = v1.read_namespaced_secret(name="cert-manager-webhook-tls", namespace=namespace)
    except client.rest.ApiException as err:
        layer.status.blocked('Waiting for certificate to be created')
        return False

    layer.caas_base.pod_spec_set(
        {
            "version": 2,
            "serviceAccount": {
                "global": True,
                "rules": [
                    {
                        "apiGroups": ["admission.cert-manager.io"],
                        "resources": [
                            "certificates",
                            "certificaterequests",
                            "issuers",
                            "clusterissuers",
                        ],
                        "verbs": ["create"],
                    }
                ],
            },
            "containers": [
                {
                    "name": "cert-manager-webhook",
                    "imageDetails": {
                        "imagePath": image_info.registry_path,
                        "username": image_info.username,
                        "password": image_info.password,
                    },
                    "args": [
                        "--v=2",
                        f"--secure-port={port}",
                        "--tls-cert-file=/certs/tls.crt",
                        "--tls-private-key-file=/certs/tls.key",
                    ],
                    "ports": [{"name": "https", "containerPort": port}],
                    "config": {"POD_NAMESPACE": namespace},
                    "files": [
                        {
                            "name": "certs",
                            "mountPath": "/certs",
                            "files": {
                                "tls.crt": b64decode(secret.data['tls.crt']).decode('utf-8'),
                                "tls.key": b64decode(secret.data['tls.key']).decode('utf-8'),
                            },
                        }
                    ],
                }
            ],
        },
        k8s_resources={
            "kubernetesResources": {
                "mutatingWebhookConfigurations": {
                    "cert-manager-webhook": [
                        {
                            "name": "webhook.cert-manager.io",
                            "rules": [
                                {
                                    "apiGroups": ["cert-manager.io"],
                                    "apiVersions": ["v1alpha2"],
                                    "operations": ["CREATE", "UPDATE"],
                                    "resources": [
                                        "certificates",
                                        "issuers",
                                        "clusterissuers",
                                        "orders",
                                        "challenges",
                                        "certificaterequests",
                                    ],
                                }
                            ],
                            "failurePolicy": "Fail",
                            "clientConfig": {
                                "service": {
                                    "name": hookenv.service_name(),
                                    "namespace": namespace,
                                    "path": "/apis/webhook.cert-manager.io/v1beta1/mutations",
                                    "port": port,
                                },
                                "caBundle": secret.data['tls.crt'],
                            },
                        }
                    ]
                },
                "validatingWebhookConfigurations": {
                    "cert-manager-webhook": [
                        {
                            "name": "webhook.certmanager.k8s.io",
                            "rules": [
                                {
                                    "apiGroups": ["cert-manager.io"],
                                    "apiVersions": ["v1alpha2"],
                                    "operations": ["CREATE", "UPDATE"],
                                    "resources": [
                                        "certificates",
                                        "issuers",
                                        "clusterissuers",
                                        "certificaterequests",
                                    ],
                                }
                            ],
                            "failurePolicy": "Fail",
                            "sideEffects": "None",
                            "clientConfig": {
                                "service": {
                                    "name": hookenv.service_name(),
                                    "namespace": namespace,
                                    "path": "/apis/webhook.cert-manager.io/v1beta1/validations",
                                    "port": port,
                                },
                                "caBundle": secret.data['tls.crt'],
                            },
                        }
                    ]
                },
            }
        },
    )

    layer.status.maintenance("creating container")
    set_flag("charm.started")
