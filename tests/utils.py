import json
from subprocess import run, CalledProcessError, PIPE

import requests

AUTH = ('admin', 'foobar')


def get_session():
    sess = requests.Session()
    sess.auth = AUTH
    sess.hooks = {'response': lambda r, *args, **kwargs: r.raise_for_status()}

    return sess


def get_pub_addr():
    """Gets the public address that Ambassador is listening to."""
    try:
        status = json.loads(
            run(
                ['juju', 'status', '-m', 'default', '--format=json'], check=True, stdout=PIPE
            ).stdout
        )
        ip = status['applications']['kubernetes-worker']['units']['kubernetes-worker/0'][
            'public-address'
        ]
    except CalledProcessError:
        # Deployed on microk8s
        status = json.loads(
            run(['juju', 'status', '--format', 'json'], check=True, stdout=PIPE).stdout
        )
        ip = status['applications']['ambassador']['units']['ambassador/0']['address']

    return f'{ip}.xip.io'
