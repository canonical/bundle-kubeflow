from glob import glob
from pathlib import Path
import os

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
        prefix='/jupyter', service=hookenv.service_name(), port=hookenv.config('port')
    )


@when('layer.docker-resource.oci-image.available', 'kubeflow-profiles.available')
@when_not('charm.started')
def start_charm():
    if not hookenv.is_leader():
        hookenv.log("This unit is not a leader.")
        return False

    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    port = hookenv.config('port')

    profiles = endpoint_from_name('kubeflow-profiles').services()[0]
    profiles_host = profiles['service_name']
    profiles_port = profiles['hosts'][0]['port']
    model = os.environ['JUJU_MODEL_NAME']

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
            'serviceAccount': {
                'global': True,
                'rules': [
                    {
                        'apiGroups': [''],
                        'resources': ['namespaces'],
                        'verbs': ['get', 'list', 'create', 'delete'],
                    },
                    {
                        'apiGroups': ['kubeflow.org'],
                        'resources': ['notebooks', 'poddefaults'],
                        'verbs': ['get', 'list', 'create', 'delete'],
                    },
                    {
                        'apiGroups': [''],
                        'resources': ['persistentvolumeclaims'],
                        'verbs': ['create', 'delete', 'get', 'list'],
                    },
                    {
                        'apiGroups': ['storage.k8s.io'],
                        'resources': ['storageclasses'],
                        'verbs': ['get', 'list', 'watch'],
                    },
                    {
                        'apiGroups': [''],
                        'resources': ['pods', 'pods/log', 'secrets', 'services'],
                        'verbs': ['*'],
                    },
                    {
                        'apiGroups': ['', 'apps', 'extensions'],
                        'resources': ['deployments', 'replicasets'],
                        'verbs': ['*'],
                    },
                    {'apiGroups': ['kubeflow.org'], 'resources': ['*'], 'verbs': ['*']},
                    {'apiGroups': ['batch'], 'resources': ['jobs'], 'verbs': ['*']},
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
                    'ports': [{'name': 'http', 'containerPort': port}],
                    'config': {
                        'USERID_HEADER': 'kubeflow-userid',
                        'USERID_PREFIX': '',
                        'KFAM': f'{profiles_host}.{model}.svc.cluster.local:{profiles_port}',
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
