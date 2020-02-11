import os

import yaml

from charms import layer
from charms.reactive import clear_flag, hook, set_flag, when, when_any, when_not
from charmhelpers.core import hookenv


@hook("upgrade-charm")
def upgrade_charm():
    clear_flag("charm.started")


@when("charm.started")
def charm_ready():
    layer.status.active("")


@when('oidc-client.available')
def configure_oidc(oidc):
    oidc.configure(
        {
            'id': hookenv.config('client-id'),
            'name': hookenv.config('client-name'),
            'redirectURIs': [hookenv.config('public-url') + '/oidc/login/oidc'],
            'secret': hookenv.config('client-secret'),
        }
    )


@when_any("layer.docker-resource.oci-image.changed", "config.changed")
def update_image():
    clear_flag("charm.started")


@when("layer.docker-resource.oci-image.available")
@when_not("charm.started")
def start_charm():
    layer.status.maintenance("configuring container")

    image_info = layer.docker_resource.get_info("oci-image")

    service_name = hookenv.service_name()
    namespace = os.environ["JUJU_MODEL_NAME"]
    public_url = hookenv.config("public-url")
    port = hookenv.config("port")
    oidc_scopes = hookenv.config("oidc-scopes")

    layer.caas_base.pod_spec_set(
        {
            "version": 2,
            "service": {
                "annotations": {
                    "getambassador.io/config": yaml.dump_all(
                        [
                            {
                                "apiVersion": "ambassador/v1",
                                "kind": "Mapping",
                                "name": "oidc-gatekeeper",
                                "prefix": "/oidc",
                                "service": f"{service_name}.{namespace}:{port}",
                                "timeout_ms": 30000,
                                "bypass_auth": True,
                            },
                            {
                                "apiVersion": "ambassador/v1",
                                "kind": "AuthService",
                                "name": "oidc-gatekeeper-auth",
                                "auth_service": f"{service_name}.{namespace}:{port}",
                                "allowed_authorization_headers": ["kubeflow-userid"],
                            },
                        ]
                    )
                }
            },
            "containers": [
                {
                    "name": "oidc-gatekeeper",
                    "imageDetails": {
                        "imagePath": image_info.registry_path,
                        "username": image_info.username,
                        "password": image_info.password,
                    },
                    "ports": [{"name": "http", "containerPort": port}],
                    "config": {
                        "CLIENT_ID": hookenv.config('client-id'),
                        "CLIENT_SECRET": hookenv.config("client-secret"),
                        "DISABLE_USERINFO": True,
                        "OIDC_PROVIDER": f"{public_url}/dex",
                        "OIDC_SCOPES": oidc_scopes,
                        "SERVER_PORT": port,
                        "SELF_URL": f"{public_url}/oidc",
                        "USERID_HEADER": "kubeflow-userid",
                        "USERID_PREFIX": "",
                        "STORE_PATH": "bolt.db",
                        "REDIRECT_URL": f"{public_url}/oidc/login/oidc",
                    },
                }
            ],
        }
    )

    layer.status.maintenance("creating container")
    set_flag("charm.started")
