import os
from pathlib import Path
from subprocess import run

from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import set_flag, clear_flag, when, when_not


@when('charm.cert-manager-webhook.started')
def charm_ready():
    layer.status.active('')


@when('layer.docker-resource.oci-image.changed', 'config.changed')
def update_image():
    clear_flag('charm.cert-manager-webhook.started')


@when('layer.docker-resource.oci-image.available')
@when_not('charm.cert-manager-webhook.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    namespace = os.environ['JUJU_MODEL_NAME']
    port = hookenv.config('port')

    run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:4096",
            "-keyout",
            "tls.key",
            "-out",
            "tls.crt",
            "-days",
            "365",
            "-subj",
            "/CN=localhost",
            "-nodes",
        ],
        check=True,
    )

    layer.caas_base.pod_spec_set(
        {
            'containers': [
                {
                    'name': 'cert-manager-webhook',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'args': [
                        '--v=2',
                        f'--secure-port={port}',
                        '--tls-cert-file=/certs/tls.crt',
                        '--tls-private-key-file=/certs/tls.key',
                    ],
                    'ports': [{'name': 'https', 'containerPort': port}],
                    'config': {'POD_NAMESPACE': namespace},
                    'files': [
                        {
                            'name': 'certs',
                            'mountPath': '/certs',
                            'files': {
                                'tls.crt': Path('tls.crt').read_text(),
                                'tls.key': Path('tls.key').read_text(),
                            },
                        }
                    ],
                }
            ]
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.cert-manager-webhook.started')
