#!/usr/bin/env python3
# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import kfp
from kfp import dsl
from kubernetes import client as k8s_client


def attach_output_volume(op):
    op.output_artifact_paths = {
        'mlpipeline-ui-metadata': '/output/mlpipeline-ui-metadata.json',
        'mlpipeline-metrics': '/output/mlpipeline-metrics.json',
    }

    op.add_volume(k8s_client.V1Volume(name='output', empty_dir=k8s_client.V1EmptyDirVolumeSource()))
    op.container.add_volume_mount(k8s_client.V1VolumeMount(name='output', mount_path='/output'))

    op.add_volume(
        k8s_client.V1Volume(name='tmp', empty_dir=k8s_client.V1EmptyDirVolumeSource())
    )
    op.container.add_volume_mount(
        k8s_client.V1VolumeMount(name='tmp', mount_path='/tmp')
    )

    return op

def gcs_download_op(url):
    return dsl.ContainerOp(
        name='GCS - Download',
        image='google/cloud-sdk:216.0.0',
        command=['sh', '-c'],
        arguments=['gsutil cat $0 | tee $1', url, '/tmp/results.txt'],
        file_outputs={
            'data': '/tmp/results.txt',
        }
    )


def echo_op(text, is_exit_handler=False):
    return dsl.ContainerOp(
        name='echo',
        image='library/bash:4.4.23',
        command=['sh', '-c'],
        arguments=['echo "$0"', text],
    )


@dsl.pipeline(
    name='Exit Handler',
    description='Downloads a message and prints it. The exit handler will run after the pipeline finishes (successfully or not).'
)
def download_and_print(url='gs://ml-pipeline-playground/shakespeare1.txt'):
    """A sample pipeline showing exit handler."""

    exit_task = echo_op('exit!')

    with dsl.ExitHandler(exit_task):
        download_task = gcs_download_op(url)
        echo_task = echo_op(download_task.output)

    dsl.get_pipeline_conf().add_op_transformer(attach_output_volume)

if __name__ == '__main__':
    kfp.compiler.Compiler().compile(download_and_print, __file__ + '.zip')
