import inspect
from typing import Callable

import pytest
from kfp import Client

from .pipelines.cowsay import cowsay_pipeline
from .pipelines.jupyter import jupyter_pipeline
from .pipelines.katib import katib_pipeline
from .pipelines.mnist import mnist_pipeline
from .pipelines.object_detection import object_detection_pipeline


def get_params(func):
    return {name: value.default for name, value in inspect.signature(func).parameters.items()}


@pytest.mark.parametrize(
    'name,fn',
    [
        pytest.param(
            'mnist',
            mnist_pipeline,
            marks=[pytest.mark.full, pytest.mark.lite, pytest.mark.edge],
        ),
        pytest.param(
            'cowsay',
            cowsay_pipeline,
            marks=[pytest.mark.full, pytest.mark.lite, pytest.mark.edge],
        ),
        pytest.param(
            'katib',
            katib_pipeline,
            marks=[pytest.mark.full],
        ),
        pytest.param(
            'jupyter',
            jupyter_pipeline,
            marks=[pytest.mark.full, pytest.mark.lite],
        ),
        pytest.param(
            'object_detection',
            object_detection_pipeline,
            marks=pytest.mark.gpu,
        ),
    ],
)
def test_pipelines(name: str, fn: Callable):
    """Runs each pipeline that it's been parameterized for, and waits for it to succeed."""

    client = Client('127.0.0.1:8888')
    run = client.create_run_from_pipeline_func(fn, arguments=get_params(fn))
    completed = client.wait_for_run_completion(run.run_id, timeout=3600)
    status = completed.to_dict()['run']['status']
    assert status == 'Succeeded', f'Pipeline {name} status is {status}'
