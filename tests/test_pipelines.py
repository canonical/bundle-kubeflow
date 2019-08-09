import time
from datetime import datetime
from tempfile import NamedTemporaryFile

from kfp.compiler import Compiler

from .pipelines.cowsay import sequential_pipeline
from .utils import get_session, get_pub_addr


def test_pipelines():
    sess = get_session()
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    endpoint = f'http://{get_pub_addr()}/pipeline/apis/v1beta1'
    pipeline_name = f'cowsay-{now}'
    run_name = f'Cow Say {now}'
    run_description = f"Automated testing run of pipeline {pipeline_name}"

    with NamedTemporaryFile('w+b', suffix='.tar.gz') as f:
        Compiler().compile(sequential_pipeline, f.name)
        pipeline = sess.post(
            f'{endpoint}/pipelines/upload', files={'uploadfile': f}, params={'name': pipeline_name}
        ).json()

        assert pipeline['name'] == pipeline_name
        assert pipeline['parameters'] == [
            {"name": "url", "value": "https://helloacm.com/api/fortune/"}
        ]

        pl_run = sess.post(
            f'{endpoint}/runs',
            json={
                "description": run_description,
                "name": run_name,
                "pipeline_spec": {
                    "parameters": [{"name": "url", "value": "https://helloacm.com/api/fortune/"}],
                    "pipeline_id": pipeline['id'],
                },
                "resource_references": [],
            },
        ).json()['run']

        for _ in range(30):
            try:
                pl_run = sess.get(f'{endpoint}/runs/{pl_run["id"]}').json()['run']
                assert pl_run['status'] == 'Succeeded'
                break
            except KeyError:
                print("Status not found on API response, retrying...")
                time.sleep(5)
            except AssertionError as err:
                print(err)
                time.sleep(5)
