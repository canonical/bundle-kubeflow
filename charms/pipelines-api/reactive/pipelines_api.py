import json
import os
from glob import glob
from pathlib import Path

from charms import layer
from charms.reactive import (
    clear_flag,
    endpoint_from_name,
    hook,
    hookenv,
    set_flag,
    when,
    when_any,
    when_not,
)


@hook('upgrade-charm')
def upgrade_charm():
    clear_flag('charm.started')


@when('charm.started')
def charm_ready():
    layer.status.active('')


@when('pipelines-api.available')
def configure_http(http):
    http.configure(port=hookenv.config('http-port'), hostname=hookenv.application_name())


@when_any(
    'layer.docker-resource.oci-image.changed',
    'config.changed',
    'kubeflow-profiles.changed',
    'endpoint.minio.joined',
    'mysql.changed',
    'pipelines-visualization.changed',
)
def update_image():
    clear_flag('charm.started')
    clear_flag('layer.docker-resource.oci-image.changed')
    clear_flag('config.changed')
    clear_flag('kubeflow-profiles.changed')
    clear_flag('minio.changed')
    clear_flag('mysql.changed')
    clear_flag('pipelines-visualization.changed')


@when('endpoint.service-mesh.joined')
def configure_mesh():
    endpoint_from_name('service-mesh').add_route(
        prefix='/apis/v1beta1/pipelines',
        service=hookenv.service_name(),
        port=hookenv.config('http-port'),
    )


@when(
    'layer.docker-resource.oci-image.available',
    'endpoint.minio.joined',
    'mysql.available',
)
@when_not('charm.started')
def start_charm():
    if not hookenv.is_leader():
        hookenv.log("This unit is not a leader.")
        return False

    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    mysql = endpoint_from_name('mysql')

    try:
        minio = endpoint_from_name('minio').mailman3()[0]
    except IndexError:
        layer.status.blocked('Waiting for minio relation.')
        return False

    if minio['ip'] is None:
        layer.status.blocked("Waiting for full minio relation.")
        return False

    hookenv.log("DEBUG")
    hookenv.log(minio)
    grpc_port = hookenv.config('grpc-port')
    http_port = hookenv.config('http-port')

    config_json = {
        'DBConfig': {
            'DriverName': 'mysql',
            'DataSourceName': mysql.database(),
            'Host': mysql.host(),
            'Port': mysql.port(),
            'User': 'root',
            'Password': mysql.root_password(),
            'DBName': 'mlpipeline',
        },
        'ObjectStoreConfig': {
            'Host': minio['ip'],
            'Port': minio['port'],
            'AccessKey': minio['user'],
            'SecretAccessKey': minio['password'],
            'BucketName': hookenv.config('minio-bucket-name'),
            'Secure': False,
        },
        'InitConnectionTimeout': '5s',
        "DefaultPipelineRunnerServiceAccount": "pipeline-runner",
    }

    profiles = endpoint_from_name('kubeflow-profiles')
    if profiles and profiles.services():
        profiles = profiles.services()[0]['hosts'][0]
        config_json["PROFILES_KFAM_SERVICE_HOST"] = profiles['hostname']
        config_json["PROFILES_KFAM_SERVICE_PORT"] = profiles['port']

    viz = endpoint_from_name('pipelines-visualization')
    if viz and viz.services():
        viz = viz.services()[0]['hosts'][0]
        config_json["ML_PIPELINE_VISUALIZATIONSERVER_SERVICE_HOST"] = viz['hostname']
        config_json["ML_PIPELINE_VISUALIZATIONSERVER_SERVICE_PORT"] = viz['port']
    else:
        config_json["ML_PIPELINE_VISUALIZATIONSERVER_SERVICE_HOST"] = 'foobar'
        config_json["ML_PIPELINE_VISUALIZATIONSERVER_SERVICE_PORT"] = '1234'

    layer.caas_base.pod_spec_set(
        {
            'version': 3,
            'serviceAccount': {
                'roles': [
                    {
                        'rules': [
                            {
                                'apiGroups': ['argoproj.io'],
                                'resources': ['workflows'],
                                'verbs': [
                                    'create',
                                    'get',
                                    'list',
                                    'watch',
                                    'update',
                                    'patch',
                                    'delete',
                                ],
                            },
                            {
                                'apiGroups': ['kubeflow.org'],
                                'resources': ['scheduledworkflows'],
                                'verbs': ['create', 'get', 'list', 'update', 'patch', 'delete'],
                            },
                            {'apiGroups': [''], 'resources': ['pods'], 'verbs': ['delete']},
                        ]
                    }
                ]
            },
            'containers': [
                {
                    'name': 'pipelines-api',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'ports': [
                        {'name': 'grpc', 'containerPort': grpc_port},
                        {'name': 'http', 'containerPort': http_port},
                    ],
                    'command': [
                        'apiserver',
                        '--config=/config',
                        '--sampleconfig=/config/sample_config.json',
                        '-logtostderr=true',
                    ],
                    'envConfig': {'POD_NAMESPACE': os.environ['JUJU_MODEL_NAME']},
                    'volumeConfig': [
                        {
                            'name': 'config',
                            'mountPath': '/config',
                            'files': [
                                {'path': 'config.json', 'content': json.dumps(config_json)},
                                {
                                    'path': 'sample_config.json',
                                    'content': Path('files/sample_config.json').read_text(),
                                },
                            ],
                        },
                        {
                            'name': 'samples',
                            'mountPath': '/samples',
                            'files': [
                                {'path': Path(sample).name, 'content': Path(sample).read_text()}
                                for sample in glob('files/*.yaml')
                            ],
                        },
                    ],
                }
            ],
        },
        k8s_resources={
            'kubernetesResources': {
                'serviceAccounts': [
                    {
                        'name': 'pipeline-runner',
                        'roles': [
                            {
                                'name': 'pipeline-runner',
                                'global': True,
                                'rules': [
                                    {'apiGroups': [''], 'resources': ['secrets'], 'verbs': ['get']},
                                    {
                                        'apiGroups': [''],
                                        'resources': ['configmaps'],
                                        'verbs': ['get', 'watch', 'list'],
                                    },
                                    {
                                        'apiGroups': [''],
                                        'resources': ['persistentvolumeclaims'],
                                        'verbs': ['create', 'delete', 'get'],
                                    },
                                    {
                                        'apiGroups': ['snapshot.storage.k8s.io'],
                                        'resources': ['volumesnapshots'],
                                        'verbs': ['create', 'delete', 'get'],
                                    },
                                    {
                                        'apiGroups': ['argoproj.io'],
                                        'resources': ['workflows'],
                                        'verbs': ['get', 'list', 'watch', 'update', 'patch'],
                                    },
                                    {
                                        'apiGroups': [''],
                                        'resources': ['pods', 'pods/exec', 'pods/log', 'services'],
                                        'verbs': ['*'],
                                    },
                                    {
                                        'apiGroups': ['', 'apps', 'extensions'],
                                        'resources': ['deployments', 'replicasets'],
                                        'verbs': ['*'],
                                    },
                                    {
                                        'apiGroups': ['kubeflow.org'],
                                        'resources': ['*'],
                                        'verbs': ['*'],
                                    },
                                    {'apiGroups': ['batch'], 'resources': ['jobs'], 'verbs': ['*']},
                                ],
                            }
                        ],
                    }
                ]
            }
        },
    )

    layer.status.maintenance('creating container')
    clear_flag('mysql.changed')
    set_flag('charm.started')
