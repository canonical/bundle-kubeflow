import random
import string
import subprocess
import typing
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import yaml

from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import clear_flag, endpoint_from_name, hook, set_flag, when, when_any, when_not

try:
    import bcrypt
except ImportError:
    subprocess.check_call(["apt", "update"])
    subprocess.check_call(["apt", "install", "-y", "python3-bcrypt"])
    import bcrypt


@hook("upgrade-charm")
def upgrade_charm():
    clear_flag("charm.started")


@when("charm.started")
def charm_ready():
    layer.status.active("")


@when("endpoint.oidc-client.changed")
def update_relation():
    clear_flag("charm.started")
    clear_flag("endpoint.oidc-client.changed")


@when_any("layer.docker-resource.oci-image.changed", "config.changed")
def update_image():
    clear_flag("charm.started")
    clear_flag("layer.docker-resource.oci-image.changed")
    clear_flag("config.changed")


@when('endpoint.service-mesh.joined')
def configure_mesh():
    endpoint_from_name('service-mesh').add_route(
        prefix='/dex', service=hookenv.service_name(), port=hookenv.config('port')
    )


def get_or_set(name: str, *, default: typing.Union[str, typing.Callable[[], str]]) -> str:
    try:
        path = Path(f'/run/{name}')
        return path.read_text()
    except FileNotFoundError:
        value = default() if callable(default) else default
        path.write_text(value)
        return value


def get_or_set_bytes(
    name: str, *, default: typing.Union[bytes, typing.Callable[[], bytes]]
) -> bytes:
    try:
        path = Path(f'/run/{name}')
        return path.read_bytes()
    except FileNotFoundError:
        value = default() if callable(default) else default
        path.write_bytes(value)
        return value


@when("layer.docker-resource.oci-image.available")
@when_not("charm.started")
def start_charm():
    if not hookenv.is_leader():
        hookenv.log("This unit is not a leader.")
        return False

    layer.status.maintenance("configuring container")

    image_info = layer.docker_resource.get_info("oci-image")

    connectors = yaml.safe_load(hookenv.config("connectors"))
    port = hookenv.config("port")
    public_url = hookenv.config("public-url")

    oidc_client = endpoint_from_name('oidc-client')
    if oidc_client:
        oidc_client_info = oidc_client.get_config()
    else:
        oidc_client_info = []

    # Allows setting a basic username/password combo
    static_username = hookenv.config("static-username")
    static_password = hookenv.config("static-password")

    static_config = {}

    # Dex needs some way of logging in, so if nothing has been configured,
    # just generate a username/password
    if not static_username:
        static_username = get_or_set('username', default='admin')

    if static_username:
        if not static_password:
            static_password = get_or_set(
                'password',
                default=lambda: ''.join(random.choices(string.ascii_letters, k=30)),
            )

        salt = get_or_set_bytes('salt', default=bcrypt.gensalt)
        user_id = get_or_set('user-id', default=lambda: str(uuid4()))

        hashed = bcrypt.hashpw(static_password.encode('utf-8'), salt).decode('utf-8')
        static_config = {
            'enablePasswordDB': True,
            'staticPasswords': [
                {
                    'email': static_username,
                    'hash': hashed,
                    'username': static_username,
                    'userID': user_id,
                }
            ],
        }

    config = yaml.dump(
        {
            "issuer": f"{public_url}/dex",
            "storage": {"type": "kubernetes", "config": {"inCluster": True}},
            "web": {"http": f"0.0.0.0:{port}"},
            "logger": {"level": "debug", "format": "text"},
            "oauth2": {"skipApprovalScreen": True},
            "staticClients": oidc_client_info,
            "connectors": connectors,
            **static_config,
        }
    )

    # Kubernetes won't automatically restart the pod when the configmap changes
    # unless we manually add the hash somewhere into the Deployment spec, so that
    # it changes whenever the configmap changes.
    config_hash = sha256()
    config_hash.update(config.encode('utf-8'))

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
            "containers": [
                {
                    "name": 'dex-auth',
                    "imageDetails": {
                        "imagePath": image_info.registry_path,
                        "username": image_info.username,
                        "password": image_info.password,
                    },
                    "command": ["dex", "serve", "/etc/dex/cfg/config.yaml"],
                    "ports": [{"name": "http", "containerPort": port}],
                    "config": {"CONFIG_HASH": config_hash.hexdigest()},
                    "files": [
                        {
                            "name": "config",
                            "mountPath": "/etc/dex/cfg",
                            "files": {"config.yaml": config},
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
