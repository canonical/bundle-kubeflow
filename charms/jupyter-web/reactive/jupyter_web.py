from glob import glob
from pathlib import Path

from charmhelpers.core import hookenv
from charms import layer
from charms.reactive import clear_flag, endpoint_from_name, hook, set_flag, when, when_any, when_not


@hook('upgrade-charm')
def upgrade_charm():
    clear_flag('charm.started')


@when('charm.started')
def charm_ready():
    layer.status.active('')


@when_any('layer.docker-resource.oci-image.changed', 'config.changed')
def update_image():
    clear_flag('charm.started')


@when('endpoint.service-mesh.joined')
def configure_mesh():
    endpoint_from_name('service-mesh').add_route(
        prefix='/jupyter/',
        rewrite='/',
        service=hookenv.service_name(),
        port=hookenv.config('port'),
    )


@when('layer.docker-resource.oci-image.available')
@when_not('charm.started')
def start_charm():
    if not hookenv.is_leader():
        hookenv.log("This unit is not a leader.")
        return False

    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    port = hookenv.config('port')

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
            'serviceAccount': {
                'global': True,
                'rules': [
                    {
                        'apiGroups': [''],
                        'resources': ['pods', 'pods/log', 'secrets', 'services'],
                        'verbs': ['*'],
                    },
                    {
                        'apiGroups': [''],
                        'resources': ['persistentvolumeclaims'],
                        'verbs': ['create', 'delete', 'get', 'list'],
                    },
                    {
                        'apiGroups': [''],
                        'resources': ['namespaces'],
                        'verbs': ['get', 'list', 'create', 'delete'],
                    },
                    {
                        'apiGroups': [''],
                        'resources': ['events'],
                        'verbs': ['list'],
                    },
                    {
                        'apiGroups': ['', 'apps', 'extensions'],
                        'resources': ['deployments', 'replicasets'],
                        'verbs': ['*'],
                    },
                    {
                        'apiGroups': ['authorization.k8s.io'],
                        'resources': ['subjectaccessreviews'],
                        'verbs': ['create'],
                    },
                    {
                        'apiGroups': ['batch'],
                        'resources': ['jobs'],
                        'verbs': ['*'],
                    },
                    {
                        'apiGroups': ['kubeflow.org'],
                        'resources': ['*'],
                        'verbs': ['*'],
                    },
                    {
                        'apiGroups': ['kubeflow.org'],
                        'resources': ['notebooks', 'notebooks/finalizers', 'poddefaults'],
                        'verbs': ['get', 'list', 'create', 'delete'],
                    },
                    {
                        'apiGroups': ['storage.k8s.io'],
                        'resources': ['storageclasses'],
                        'verbs': ['get', 'list', 'watch'],
                    },
                ],
            },
            'containers': [
                {
                    'name': 'jupyter-web',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'command': ['python3'],
                    'args': ['main.py', '--dev'],
                    'ports': [{'name': 'http', 'containerPort': port}],
                    'config': {
                        'USERID_HEADER': 'kubeflow-userid',
                        'USERID_PREFIX': '',
                    },
                    'files': [
                        {
                            'name': 'configs',
                            'mountPath': '/etc/config',
                            'files': {
                                Path(filename).name: Path(filename).read_text()
                                for filename in glob('files/*')
                            },
                        }
                    ],
                }
            ],
        }
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
