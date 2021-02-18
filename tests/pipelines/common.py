from kubernetes import client as k8s_client


def attach_output_volume(op):
    """Attaches emptyDir volumes to container operations.

    See https://github.com/kubeflow/pipelines/issues/1654
    """

    # Handle auto-generated pipeline metadata
    op.output_artifact_paths['mlpipeline-ui-metadata'] = '/tmp/outputs/mlpipeline-ui-metadata.json'
    op.output_artifact_paths['mlpipeline-metrics'] = '/tmp/outputs/mlpipeline-metrics.json'

    # Add somewhere to store regular output
    op.add_volume(k8s_client.V1Volume(name='volume', empty_dir=k8s_client.V1EmptyDirVolumeSource()))
    op.container.add_volume_mount(k8s_client.V1VolumeMount(name='volume', mount_path='/output'))

    # func_to_container_op wants to store outputs under /tmp/outputs
    op.add_volume(
        k8s_client.V1Volume(name='outputs', empty_dir=k8s_client.V1EmptyDirVolumeSource())
    )
    op.container.add_volume_mount(
        k8s_client.V1VolumeMount(name='outputs', mount_path='/tmp/outputs')
    )

    return op
