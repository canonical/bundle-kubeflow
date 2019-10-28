import yaml
from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import hook, set_flag, clear_flag, when, when_not


@hook('upgrade-charm')
def upgrade_charm():
    clear_flag('charm.started')


@when('charm.started')
def charm_ready():
    layer.status.active('')


@when('layer.docker-resource.oci-image.changed')
def update_image():
    clear_flag('charm.started')


@when('layer.docker-resource.oci-image.available')
@when_not('charm.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
            'serviceAccount': {
                'rules': [
                    {'apiGroups': [''], 'resources': ['configmaps'], 'verbs': ['*']},
                    {'apiGroups': ['kubeflow.org'], 'resources': ['studyjobs'], 'verbs': ['*']},
                ]
            },
            'service': {
                'annotations': {
                    'getambassador.io/config': yaml.dump_all(
                        [
                            {
                                'apiVersion': 'ambassador/v0',
                                'kind': 'Mapping',
                                'name': 'katib-ui',
                                'prefix': '/katib/',
                                'rewrite': '/katib/',
                                'service': f'{hookenv.service_name()}:80',
                                'timeout_ms': 30000,
                            }
                        ]
                    )
                }
            },
            'containers': [
                {
                    'name': 'katib-ui',
                    'command': ["./katib-ui"],
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'ports': [{'name': 'port', 'containerPort': 80}],
                }
            ],
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
