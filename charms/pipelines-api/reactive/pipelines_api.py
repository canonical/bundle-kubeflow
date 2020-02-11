import json
import os
from glob import glob
from pathlib import Path

import yaml

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


@when_any('layer.docker-resource.oci-image.changed', 'config.changed', 'mysql.changed')
def update_image():
    clear_flag('charm.started')


@when(
    'layer.docker-resource.oci-image.available',
    'kubeflow-profiles.available',
    'minio.available',
    'mysql.available',
    'pipelines-visualization.available',
)
@when_not('charm.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')
    service_name = hookenv.service_name()

    minio = endpoint_from_name('minio').services()[0]['hosts'][0]
    mysql = endpoint_from_name('mysql')
    profiles = endpoint_from_name('kubeflow-profiles').services()[0]['hosts'][0]
    viz = endpoint_from_name('pipelines-visualization').services()[0]['hosts'][0]

    grpc_port = hookenv.config('grpc-port')
    http_port = hookenv.config('http-port')

    layer.caas_base.pod_spec_set(
        {
            'version': 2,
            'serviceAccount': {
                'rules': [
                    {
                        'apiGroups': ['argoproj.io'],
                        'resources': ['workflows'],
                        'verbs': ['create', 'get', 'list', 'watch', 'update', 'patch', 'delete'],
                    },
                    {
                        'apiGroups': ['kubeflow.org'],
                        'resources': ['scheduledworkflows'],
                        'verbs': ['create', 'get', 'list', 'update', 'patch', 'delete'],
                    },
                    {'apiGroups': [''], 'resources': ['pods'], 'verbs': ['delete']},
                ]
            },
            'service': {
                'annotations': {
                    'getambassador.io/config': yaml.dump_all(
                        [
                            {
                                'apiVersion': 'ambassador/v0',
                                'kind': 'Mapping',
                                'name': 'pipeline-api',
                                'prefix': '/apis/v1beta1/pipelines',
                                'rewrite': '/apis/v1beta1/pipelines',
                                'service': f'{service_name}:{http_port}',
                                'use_websocket': True,
                                'timeout_ms': 30000,
                            }
                        ]
                    )
                }
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
                    'config': {'POD_NAMESPACE': os.environ['JUJU_MODEL_NAME']},
                    'files': [
                        {
                            'name': 'config',
                            'mountPath': '/config',
                            'files': {
                                'config.json': json.dumps(
                                    {
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
                                            'Host': minio['hostname'],
                                            'Port': minio['port'],
                                            'AccessKey': hookenv.config('minio-access-key'),
                                            'SecretAccessKey': hookenv.config('minio-secret-key'),
                                            'BucketName': hookenv.config('minio-bucket-name'),
                                        },
                                        'InitConnectionTimeout': '5s',
                                        "DefaultPipelineRunnerServiceAccount": "pipeline-runner",
                                        "ML_PIPELINE_VISUALIZATIONSERVER_SERVICE_HOST": viz[
                                            'hostname'
                                        ],
                                        "ML_PIPELINE_VISUALIZATIONSERVER_SERVICE_PORT": viz['port'],
                                        'PROFILES_KFAM_SERVICE_HOST': profiles['hostname'],
                                        'PROFILES_KFAM_SERVICE_PORT': profiles['port'],
                                    }
                                ),
                                'sample_config.json': Path('files/sample_config.json').read_text(),
                            },
                        },
                        {
                            'name': 'samples',
                            'mountPath': '/samples',
                            'files': {
                                Path(sample).name: Path(sample).read_text()
                                for sample in glob('files/*.yaml')
                            },
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
                            {'apiGroups': ['kubeflow.org'], 'resources': ['*'], 'verbs': ['*']},
                            {'apiGroups': ['batch'], 'resources': ['jobs'], 'verbs': ['*']},
                        ],
                    }
                ]
            }
        },
    )

    layer.status.maintenance('creating container')
    clear_flag('mysql.changed')
    set_flag('charm.started')
