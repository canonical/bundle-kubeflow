import os
from pathlib import Path

import yaml

from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import clear_flag, hook, set_flag, when, when_any, when_not, endpoint_from_name


@hook("upgrade-charm")
def upgrade_charm():
    clear_flag("charm.started")


@when("charm.started")
def charm_ready():
    layer.status.active("")


@when_any("layer.docker-resource.oci-image.changed", "config.changed")
def update_image():
    clear_flag("charm.started")


@when("layer.docker-resource.oci-image.available", "cert-manager-webhook.available")
@when_not("charm.started")
def start_charm():
    layer.status.maintenance("configuring container")

    image_info = layer.docker_resource.get_info("oci-image")
    webhook = endpoint_from_name('cert-manager-webhook').services()[0]['service_name']

    namespace = os.environ["JUJU_MODEL_NAME"]

    layer.caas_base.pod_spec_set(
        {
            "version": 2,
            "serviceAccount": {
                "global": True,
                "rules": [
                    {
                        "apiGroups": ["cert-manager.io"],
                        "resources": ["issuers", "issuers/status"],
                        "verbs": ["update"],
                    },
                    {
                        "apiGroups": ["cert-manager.io"],
                        "resources": ["issuers"],
                        "verbs": ["get", "list", "watch"],
                    },
                    {
                        "apiGroups": [""],
                        "resources": ["secrets"],
                        "verbs": ["get", "list", "watch", "create", "update", "delete"],
                    },
                    {"apiGroups": [""], "resources": ["events"], "verbs": ["create", "patch"]},
                    {
                        "apiGroups": ["cert-manager.io"],
                        "resources": ["clusterissuers", "clusterissuers/status"],
                        "verbs": ["update"],
                    },
                    {
                        "apiGroups": ["cert-manager.io"],
                        "resources": ["clusterissuers"],
                        "verbs": ["get", "list", "watch"],
                    },
                    {
                        "apiGroups": ["cert-manager.io"],
                        "resources": [
                            "certificates",
                            "certificates/status",
                            "certificaterequests",
                            "certificaterequests/status",
                        ],
                        "verbs": ["update"],
                    },
                    {
                        "apiGroups": ["cert-manager.io"],
                        "resources": [
                            "certificates",
                            "certificaterequests",
                            "clusterissuers",
                            "issuers",
                        ],
                        "verbs": ["get", "list", "watch"],
                    },
                    {
                        "apiGroups": ["cert-manager.io"],
                        "resources": ["certificates/finalizers"],
                        "verbs": ["update"],
                    },
                    {
                        "apiGroups": ["acme.cert-manager.io"],
                        "resources": ["orders"],
                        "verbs": ["create", "delete", "get", "list", "watch"],
                    },
                    {
                        "apiGroups": ["acme.cert-manager.io"],
                        "resources": ["orders", "orders/status"],
                        "verbs": ["update"],
                    },
                    {
                        "apiGroups": ["acme.cert-manager.io"],
                        "resources": ["orders", "challenges"],
                        "verbs": ["get", "list", "watch"],
                    },
                    {
                        "apiGroups": ["cert-manager.io"],
                        "resources": ["clusterissuers", "issuers"],
                        "verbs": ["get", "list", "watch"],
                    },
                    {
                        "apiGroups": ["acme.cert-manager.io"],
                        "resources": ["challenges"],
                        "verbs": ["create", "delete"],
                    },
                    {
                        "apiGroups": ["acme.cert-manager.io"],
                        "resources": ["orders/finalizers"],
                        "verbs": ["update"],
                    },
                    {
                        "apiGroups": [""],
                        "resources": ["secrets"],
                        "verbs": ["get", "list", "watch"],
                    },
                    {
                        "apiGroups": ["acme.cert-manager.io"],
                        "resources": ["challenges", "challenges/status"],
                        "verbs": ["update"],
                    },
                    {
                        "apiGroups": ["acme.cert-manager.io"],
                        "resources": ["challenges"],
                        "verbs": ["get", "list", "watch"],
                    },
                    {
                        "apiGroups": ["cert-manager.io"],
                        "resources": ["issuers", "clusterissuers"],
                        "verbs": ["get", "list", "watch"],
                    },
                    {
                        "apiGroups": [""],
                        "resources": ["secrets"],
                        "verbs": ["get", "list", "watch"],
                    },
                    {"apiGroups": [""], "resources": ["events"], "verbs": ["create", "patch"],},
                    {
                        "apiGroups": [""],
                        "resources": ["pods", "services"],
                        "verbs": ["get", "list", "watch", "create", "delete"],
                    },
                    {
                        "apiGroups": ["extensions", "networking.k8s.io/v1"],
                        "resources": ["ingresses"],
                        "verbs": ["get", "list", "watch", "create", "delete", "update"],
                    },
                    {
                        "apiGroups": ["acme.cert-manager.io"],
                        "resources": ["challenges/finalizers"],
                        "verbs": ["update"],
                    },
                    {
                        "apiGroups": [""],
                        "resources": ["secrets"],
                        "verbs": ["get", "list", "watch"],
                    },
                    {
                        "apiGroups": ["cert-manager.io"],
                        "resources": ["certificates", "certificaterequests"],
                        "verbs": ["create", "update", "delete"],
                    },
                    {
                        "apiGroups": ["cert-manager.io"],
                        "resources": [
                            "certificates",
                            "certificaterequests",
                            "issuers",
                            "clusterissuers",
                        ],
                        "verbs": ["get", "list", "watch"],
                    },
                    {
                        "apiGroups": ["networking.k8s.io/v1"],
                        "resources": ["ingresses"],
                        "verbs": ["get", "list", "watch"],
                    },
                    {
                        "apiGroups": ["networking.k8s.io/v1"],
                        "resources": ["ingresses/finalizers"],
                        "verbs": ["update"],
                    },
                    {"apiGroups": [""], "resources": ["events"], "verbs": ["create", "patch"],},
                    {
                        "apiGroups": ["cert-manager.io"],
                        "resources": ["certificates", "certificaterequests", "issuers"],
                        "verbs": ["get", "list", "watch"],
                    },
                    {
                        "apiGroups": ["cert-manager.io"],
                        "resources": ["certificates", "certificaterequests", "issuers"],
                        "verbs": ["create", "delete", "deletecollection", "patch", "update",],
                    },
                ],
            },
            "containers": [
                {
                    "name": "cert-manager-controller",
                    "imageDetails": {
                        "imagePath": image_info.registry_path,
                        "username": image_info.username,
                        "password": image_info.password,
                    },
                    "args": [
                        "--v=2",
                        f"--cluster-resource-namespace={namespace}",
                        "--leader-election-namespace=kube-system",
                        f"--webhook-namespace={namespace}",
                        "--webhook-ca-secret=cert-manager-webhook-ca",
                        "--webhook-serving-secret=cert-manager-webhook-tls",
                        f"--webhook-dns-names={webhook},{webhook}.{namespace},{webhook}.{namespace}.svc",
                    ],
                    "config": {"POD_NAMESPACE": namespace},
                    "ports": [{"name": "http", "containerPort": hookenv.config("port")}],
                }
            ],
        },
        {
            "kubernetesResources": {
                "customResourceDefinitions": {
                    crd["metadata"]["name"]: crd["spec"]
                    for crd in yaml.safe_load_all(Path("resources/crds.yaml").read_text())
                },
                'customResources': {
                    'issuers.cert-manager.io': [
                        {
                            'apiVersion': 'cert-manager.io/v1alpha2',
                            'kind': 'Issuer',
                            'metadata': {'name': 'self-signed'},
                            'spec': {'selfSigned': {}},
                        }
                    ]
                },
            }
        },
    )

    layer.status.maintenance("creating container")
    set_flag("charm.started")
