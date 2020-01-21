import os
from pathlib import Path
from uuid import uuid4
import bcrypt
import yaml

from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import clear_flag, endpoint_from_name, hook, set_flag, when, when_any, when_not


@hook("upgrade-charm")
def upgrade_charm():
    clear_flag("charm.started")


@when("charm.started")
def charm_ready():
    layer.status.active("")


@when_any("layer.docker-resource.oci-image.changed", "config.changed")
def update_image():
    clear_flag("charm.started")


@when("layer.docker-resource.oci-image.available", "oidc-client.available")
@when_not("charm.started")
def start_charm():
    layer.status.maintenance("configuring container")

    image_info = layer.docker_resource.get_info("oci-image")

    service_name = hookenv.service_name()
    connectors = yaml.safe_load(hookenv.config("connectors"))
    namespace = os.environ["JUJU_MODEL_NAME"]
    oidc_client_info = endpoint_from_name('oidc-client').get_config()
    port = hookenv.config("port")
    public_url = hookenv.config("public-url")

    # Allows setting a basic username/password combo
    static_username = hookenv.config("static-username")
    static_password = hookenv.config("static-password")

    static_config = {}

    if static_username:
        if not static_password:
            layer.status.blocked('Static password is required when static username is set')
            return False

        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(static_password.encode('utf-8'), salt).decode('utf-8')
        static_config = {
            'enablePasswordDB': True,
            'staticPasswords': [
                {
                    'email': static_username,
                    'hash': hashed,
                    'username': static_username,
                    'userID': str(uuid4()),
                }
            ],
        }

    layer.caas_base.pod_spec_set(
        {
            "version": 2,
            "serviceAccount": {
                "global": True,
                "rules": [
                    {"apiGroups": ["dex.coreos.com"], "resources": ["*"], "verbs": ["*"]},
                    {
                        "apiGroups": ["apiextensions.k8s.io"],
                        "resources": ["customresourcedefinitions"],
                        "verbs": ["create"],
                    },
                ],
            },
            "service": {
                "annotations": {
                    "getambassador.io/config": yaml.dump_all(
                        [
                            {
                                "apiVersion": "ambassador/v1",
                                "kind": "Mapping",
                                "name": "dex-auth",
                                "prefix": "/dex",
                                "rewrite": "/dex",
                                "service": f"{service_name}.{namespace}:{port}",
                                "timeout_ms": 30000,
                                "bypass_auth": True,
                            }
                        ]
                    )
                }
            },
            "containers": [
                {
                    "name": "dex-auth",
                    "imageDetails": {
                        "imagePath": image_info.registry_path,
                        "username": image_info.username,
                        "password": image_info.password,
                    },
                    "command": ["dex", "serve", "/etc/dex/cfg/config.yaml"],
                    "ports": [{"name": "http", "containerPort": port}],
                    "files": [
                        {
                            "name": "config",
                            "mountPath": "/etc/dex/cfg",
                            "files": {
                                "config.yaml": yaml.dump(
                                    {
                                        "issuer": f"{public_url}/dex",
                                        "storage": {
                                            "type": "kubernetes",
                                            "config": {"inCluster": True},
                                        },
                                        "web": {"http": f"0.0.0.0:{port}"},
                                        "logger": {"level": "debug", "format": "text"},
                                        "oauth2": {"skipApprovalScreen": True},
                                        "staticClients": oidc_client_info,
                                        "connectors": connectors,
                                        **static_config,
                                    }
                                )
                            },
                        }
                    ],
                }
            ],
        },
        {
            "kubernetesResources": {
                "customResourceDefinitions": {
                    crd["metadata"]["name"]: crd["spec"]
                    for crd in yaml.safe_load_all(Path("resources/crds.yaml").read_text())
                }
            }
        },
    )

    layer.status.maintenance("creating container")
    set_flag("charm.started")
