import json
import time
from datetime import datetime
from tempfile import NamedTemporaryFile
from subprocess import run, CalledProcessError

from kfp.compiler import Compiler

from .pipelines.cowsay import sequential_pipeline
from .session import get_session


def get_pub_ip():
    """Gets the public IP address that Ambassador is listening to."""
    try:
        status = json.loads(
            run(
                ['juju', 'status', '-m', 'default', '--format=json'],
                check=True,
                capture_output=True,
            ).stdout
        )
        return status['applications']['kubernetes-worker']['units']['kubernetes-worker/0'][
            'public-address'
        ]
    except CalledProcessError:
        # Deployed on microk8s
        status = json.loads(
            run(['juju', 'status', '--format', 'json'], check=True, capture_output=True).stdout
        )
        return status['applications']['ambassador']['units']['ambassador/0']['address']


def test_pipelines():
    sess = get_session()
    pub_ip = get_pub_ip()
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    endpoint = f'http://{pub_ip}.xip.io/pipeline/apis/v1beta1'
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
