from pathlib import Path
from random import choices
from string import ascii_uppercase, digits

from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import clear_flag, endpoint_from_name, hook, set_flag, when, when_any, when_not


@hook("upgrade-charm")
def upgrade_charm():
    clear_flag("charm.started")


@when("charm.started")
def charm_ready():
    layer.status.active("")


@when('endpoint.service-mesh.joined')
def configure_mesh():
    endpoint_from_name('service-mesh').add_route(
        prefix='/authservice', service=hookenv.service_name(), port=hookenv.config('port')
    )


@when('oidc-client.available')
def configure_oidc(oidc):
    config = dict(hookenv.config())

    if not config.get('public-url'):
        return False

    if not Path('/run/password').exists():
        Path('/run/password').write_text(''.join(choices(ascii_uppercase + digits, k=30)))

    oidc.configure(
        {
            'id': config['client-id'],
            'name': config['client-name'],
            'redirectURIs': ['/authservice/oidc/callback'],
            'secret': Path('/run/password').read_text(),
        }
    )


@when_any("layer.docker-resource.oci-image.changed", "config.changed")
def update_image():
    clear_flag("charm.started")


@when("layer.docker-resource.oci-image.available")
@when_not("charm.started")
def start_charm():
    if not hookenv.is_leader():
        hookenv.log("This unit is not a leader.")
        return False

    layer.status.maintenance("configuring container")

    if not Path('/run/password').exists():
        Path('/run/password').write_text(''.join(choices(ascii_uppercase + digits, k=30)))

    image_info = layer.docker_resource.get_info("oci-image")

    public_url = hookenv.config("public-url")
    port = hookenv.config("port")
    oidc_scopes = hookenv.config("oidc-scopes")

    layer.caas_base.pod_spec_set(
        {
            "version": 2,
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
                        "CLIENT_SECRET": Path('/run/password').read_text(),
                        "DISABLE_USERINFO": True,
                        "OIDC_PROVIDER": f"{public_url}/dex",
                        "OIDC_SCOPES": oidc_scopes,
                        "SERVER_PORT": port,
                        "USERID_HEADER": "kubeflow-userid",
                        "USERID_PREFIX": "",
                        "SESSION_STORE_PATH": "bolt.db",
                        'SKIP_AUTH_URLS': '/dex/',
                        'AUTHSERVICE_URL_PREFIX': '/authservice/',
                    },
                }
            ],
        }
    )

    layer.status.maintenance("creating container")
    set_flag("charm.started")
