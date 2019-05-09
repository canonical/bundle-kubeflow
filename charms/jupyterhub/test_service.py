import base64
import time

import requests

URL = 'http://localhost:8081'
USER = 'travisci'


def get_token():
    """Generates a token for `USER`.

    Expects `DummyAuthenticator` to be used, and logs in to ensure user is created.
    """
    response = requests.post(f'{URL}/hub/login', data={'username': USER})
    response.raise_for_status()

    response = requests.post(
        f'{URL}/hub/api/users/{USER}/tokens',
        json={'note': 'travisci'},
        cookies=response.history[0].cookies,
        headers={'referer': f'{URL}/hub/token'})
    response.raise_for_status()

    return response.json()['token']


def test_version():
    """Checks the that version matches what we expect"""

    response = requests.get(f'{URL}/hub/api/')
    response.raise_for_status()
    assert response.json() == {'version': '1.0.0.dev'}


def test_jupyterhub():
    """Spins up a Jupyter notebook instance for `USER`

    Uploads a sample file to ensure connectivity.
    """

    token = get_token()

    response = requests.post(
        f'{URL}/hub/spawn',
        headers={'Authorization': 'token %s' % token},
        files={
            "imageType": "standard",
            "image": "gcr.io/kubeflow-images-public/tensorflow-1.12.0-notebook-cpu:v0.4.0",
            "cpu": "1.0",
            "memory": "1.0Gi",
            "ws_type": "New",
            "ws_name": f"{USER}-workspace",
            "ws_size": "1",
            "ws_mount_path": "/home/jovyan",
            "ws_access_modes": "ReadWriteOnce",
            "extraResources": "{}",
        })
    response.raise_for_status()
