from typing import Callable

import pytest
from kfp import Client

from .pipelines.cowsay import cowsay_pipeline
from .pipelines.mnist import mnist_pipeline
from .pipelines.katib import katib_pipeline
from .pipelines.jupyter import jupyter_pipeline
from .pipelines.object_detection import object_detection_pipeline


COWSAY_PARAMS = [{}]


MNIST_PARAMS = [
    {
        'name': 'test_images',
        'value': 'https://people.canonical.com/~knkski/t10k-images-idx3-ubyte.gz',
    },
    {
        'name': 'test_labels',
        'value': 'https://people.canonical.com/~knkski/t10k-labels-idx1-ubyte.gz',
    },
    {'name': 'train_batch_size', 'value': '128'},
    {'name': 'train_epochs', 'value': '2'},
    {
        'name': 'train_images',
        'value': 'https://people.canonical.com/~knkski/train-images-idx3-ubyte.gz',
    },
    {
        'name': 'train_labels',
        'value': 'https://people.canonical.com/~knkski/train-labels-idx1-ubyte.gz',
    },
]

KATIB_PARAMS = [
    {
        'name': 'example',
        'value': 'https://raw.githubusercontent.com/kubeflow/katib/4559e16/examples/v1alpha3/grid-example.yaml',
    }
]
OBJ_DET_PARAMS = []

JUPYTER_PARAMS = []


@pytest.mark.parametrize(
    'name,params,fn',
    [
        pytest.param(
            'mnist',
            MNIST_PARAMS,
            mnist_pipeline,
            marks=[pytest.mark.full, pytest.mark.lite, pytest.mark.edge],
        ),
        pytest.param(
            'cowsay',
            COWSAY_PARAMS,
            cowsay_pipeline,
            marks=[pytest.mark.full, pytest.mark.lite, pytest.mark.edge],
        ),
        pytest.param(
            'katib',
            KATIB_PARAMS,
            katib_pipeline,
            marks=[pytest.mark.full],
        ),
        pytest.param(
            'jupyter',
            JUPYTER_PARAMS,
            jupyter_pipeline,
            marks=[pytest.mark.full, pytest.mark.lite],
        ),
        pytest.param(
            'object_detection',
            OBJ_DET_PARAMS,
            object_detection_pipeline,
            marks=pytest.mark.gpu,
        ),
    ],
)
def test_pipelines(name: str, params: list, fn: Callable):
    """Runs each pipeline that it's been parameterized for, and waits for it to succeed."""

    client = Client('127.0.0.1:8888')
    run = client.create_run_from_pipeline_func(
        fn, arguments={p['name']: p['value'] for p in params}
    )
    completed = client.wait_for_run_completion(run.run_id, timeout=3600)
    status = completed.to_dict()['run']['status']
    assert status == 'Succeeded', f'Pipeline {name} status is {status}'
