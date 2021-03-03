from kfp import dsl
from kubernetes import client as k8s_client


def attach_output_volume(fun):
    """Attaches emptyDir volumes to container operations.

    See https://github.com/kubeflow/pipelines/issues/1654
    """

    def inner(*args, **kwargs):
        op = fun(*args, **kwargs)
        op.output_artifact_paths = {
            'mlpipeline-ui-metadata': '/output/mlpipeline-ui-metadata.json',
            'mlpipeline-metrics': '/output/mlpipeline-metrics.json',
        }
        op.add_volume(
            k8s_client.V1Volume(name='volume', empty_dir=k8s_client.V1EmptyDirVolumeSource())
        )
        op.container.add_volume_mount(k8s_client.V1VolumeMount(name='volume', mount_path='/output'))

        return op

    return inner


@attach_output_volume
def fortune_task():
    """Get a random fortune."""
    return dsl.ContainerOp(
        name='fortune',
        image='ubuntu',
        command=['sh', '-c'],
        arguments=['echo "Hello World" | tee /output/fortune.txt'],
        file_outputs={'text': '/output/fortune.txt'},
    )


@attach_output_volume
def cow_task(text):
    """Have a cow say something"""
    return dsl.ContainerOp(
        name='cowsay',
        image='chuanwen/cowsay',
        command=['bash', '-c'],
        arguments=['/usr/games/cowsay "$0" | tee $1', text, '/output/cowsay.txt'],
        file_outputs={'text': '/output/cowsay.txt'},
    )


@dsl.pipeline(name='Fortune Cow', description='Talk to a fortunate cow.')
def cowsay_pipeline():
    fortune = fortune_task()
    cow_task(fortune.output)
