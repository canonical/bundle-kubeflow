import requests

AUTH = ('admin', 'foobar')


def get_session():
    sess = requests.Session()
    sess.auth = AUTH
    sess.hooks = {
        'response': lambda r, *args, **kwargs: r.raise_for_status()
    }

    return sess
