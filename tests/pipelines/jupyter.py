"""Tests Jupyter notebook creation."""

import json
from functools import partial
from typing import NamedTuple

from kfp import components, dsl

func_to_container_op = partial(
    components.func_to_container_op,
    base_image='rocks.canonical.com:5000/kubeflow/examples/mnist-test:latest',
)


@func_to_container_op
def ensure_pd_task():
    """Ensures that a PodDefaults resource exists."""

    from kubernetes import client, config

    config.load_incluster_config()
    api = client.CustomObjectsApi()

    try:
        api.create_namespaced_custom_object(
            group="kubeflow.org",
            version="v1alpha1",
            namespace="admin",
            plural="poddefaults",
            body={
                'apiVersion': 'kubeflow.org/v1alpha1',
                'kind': 'PodDefault',
                'metadata': {'name': 'kubeflow-ci-test'},
                'spec': {
                    'selector': {'matchLabels': {'kubeflow-ci-test': 'true'}},
                    'desc': 'kubeflow ci test',
                    'env': [{'name': 'CI', 'value': 'true'}],
                },
            },
        )
    except client.rest.ApiException as err:
        if err.status == 409:
            pass
        else:
            raise


@func_to_container_op
def create_task(
    namespace: str,
    endpoint: str,
    configurations: str,
    cpu: str,
    # custom_image: str,
    custom_image_check: bool,
    datavols: str,
    extra: str,
    image: str,
    memory: str,
    no_workspace: bool,
    shm: bool,
    workspace: str,
) -> NamedTuple('Data', [('notebook_name', str)]):
    """Creates a Jupyter notebook instance."""

    import requests
    import string
    import random
    import json

    name = 'ci-' + ''.join(random.choice(string.ascii_lowercase) for _ in range(12))

    workspace = json.loads(workspace)
    workspace['name'] = workspace['name'].format(name)
    response = requests.post(
        f'{endpoint}/jupyter/api/namespaces/{namespace}/notebooks',
        json={
            "configurations": json.loads(configurations),
            "cpu": cpu,
            "customImage": '',
            "customImageCheck": custom_image_check,
            "datavols": json.loads(datavols),
            "extra": extra,
            "image": image,
            "memory": memory,
            "name": name,
            "namespace": namespace,
            "noWorkspace": no_workspace,
            "shm": shm,
            "workspace": workspace,
        },
    )
    response.raise_for_status()
    assert response.json() == {"log": "", "success": True}, f"Got bad response: {response.json()}"

    return (name,)


@func_to_container_op
def wait_task(namespace: str, endpoint: str, notebook_name: str):
    """Waits for Jupyter notebook to come up."""

    import requests
    import time

    for _ in range(240):
        response = requests.get(f'{endpoint}/jupyter/api/namespaces/{namespace}/notebooks')
        response.raise_for_status()
        notebooks = response.json()['notebooks']

        try:
            notebook = next(n for n in notebooks if n['name'] == notebook_name)
            if notebook['status'] == 'running':
                print(f"Notebook {notebook_name} is ready.")
                break
            else:
                print(f"Notebook {notebook_name} is in state {notebook['status']}...")
        except StopIteration:
            print(f"Waiting for notebook {notebook_name}...")

        time.sleep(5)
    else:
        raise Exception("Waited too long for jobs to complete!")


@func_to_container_op
def test_task(namespace: str, notebook_name: str):
    """Tests that a pod comes up correctly."""

    from kubernetes import client, config

    config.load_incluster_config()
    api = client.CoreV1Api()
    pod = api.read_namespaced_pod(f'{notebook_name}-0', namespace)

    # Ensure that admission-webhook is properly adding environment variables
    # specified by the `configurations` parameter.
    env_vars = {e.name: e.value for e in pod.spec.containers[0].env}
    assert env_vars['CI'] == 'true'


@func_to_container_op
def delete_task(namespace: str, endpoint: str, notebook_name: str):
    """Ensures Jupyter notebooks are cleaned up."""

    import requests

    response = requests.delete(
        f'{endpoint}/jupyter/api/namespaces/{namespace}/notebooks/{notebook_name}'
    )
    response.raise_for_status()


@dsl.pipeline(
    name='Jupyter Test',
    description='Tests Jupyter',
)
def jupyter_pipeline(
    namespace: str = 'admin',
    endpoint: str = 'http://jupyter-ui.kubeflow.svc.cluster.local:5000',
    notebook_configurations: str = '["kubeflow-ci-test"]',
    notebook_cpu: str = "0.5",
    # notebook_custom_image: str = "",
    notebook_custom_image_check: bool = False,
    notebook_datavols: str = '[]',
    notebook_extra: str = "{}",
    notebook_image: str = "gcr.io/kubeflow-images-public/tensorflow-1.14.0-notebook-cpu:v0.7.0",
    notebook_memory: str = "1.0Gi",
    notebook_no_workspace: bool = False,
    notebook_shm: bool = True,
    notebook_workspace: str = json.dumps(
        {
            "class": "{none}",
            "extraFields": {},
            "mode": "ReadWriteOnce",
            "name": "workspace-{0}",
            "size": "10Gi",
            "templatedName": "workspace-{notebook-name}",
            "type": "New",
        }
    ),
):
    ensure_pd = ensure_pd_task()
    create = create_task(
        namespace,
        endpoint,
        notebook_configurations,
        notebook_cpu,
        # notebook_custom_image,
        notebook_custom_image_check,
        notebook_datavols,
        notebook_extra,
        notebook_image,
        notebook_memory,
        notebook_no_workspace,
        notebook_shm,
        notebook_workspace,
    ).after(ensure_pd)

    wait = wait_task(namespace, endpoint, create.outputs['notebook_name'])
    test = test_task(namespace, create.outputs['notebook_name']).after(wait)
    delete = delete_task(namespace, endpoint, create.outputs['notebook_name']).after(test)
