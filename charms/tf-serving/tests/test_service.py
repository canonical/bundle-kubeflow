import requests

URL = 'http://localhost:9001'


def test_half_plus_two():
    """Checks the output from a basic model"""

    inputs = list(range(10))
    outputs = [i / 2 + 2 for i in inputs]

    response = requests.post(f'{URL}/v1/models/half_plus_two:predict', json={
        'instances': inputs,
    })
    response.raise_for_status()
    assert response.json() == {'predictions': outputs}
