from base64 import b64encode

import yaml
from charmhelpers import fetch
from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import hook, set_flag, clear_flag, when, when_not, when_any


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
    # Attempt to import bcrypt and install the required libraries if
    # the import fails
    try:
        import bcrypt
    except ImportError:
        layer.status.maintenance('configuring operator')
        fetch.apt_update()
        fetch.apt_install('python3-cffi-backend')
        import bcrypt

    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')
    service_name = hookenv.service_name()

    port = hookenv.config('port')
    username = hookenv.config('username')
    password = hookenv.config('password')

    if not username:
        layer.status.blocked('Setting a username is required!')
        return False

    if not password:
        layer.status.blocked('Setting a password is required!')
        return False

    password = b64encode(bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())).decode()

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
            'service': {
                'annotations': {
                    'getambassador.io/config': yaml.dump_all(
                        [
                            {
                                'apiVersion': 'ambassador/v0',
                                'kind': 'AuthService',
                                'name': 'basic-auth',
                                'auth_service': f'{service_name}:{port}',
                                'allowed_headers': ['x-from-login'],
                            }
                        ]
                    )
                }
            },
            'containers': [
                {
                    'name': 'kubeflow-gatekeeper',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'command': ['/opt/kubeflow/gatekeeper'],
                    'args': [f'--username={username}', f'--pwhash={password}'],
                    'config': {'USERNAME': username, 'PASSWORDHASH': password},
                    'ports': [{'name': 'http', 'containerPort': port}],
                }
            ],
        },
        {
            'kubernetesResources': {
                'customResources': {
                    'profiles.kubeflow.org': [
                        {
                            'apiVersion': 'kubeflow.org/v1alpha1',
                            'kind': 'Profile',
                            'metadata': {'name': username},
                            'spec': {'owner': {'kind': 'User', 'name': username}},
                        }
                    ]
                }
            }
        },
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
