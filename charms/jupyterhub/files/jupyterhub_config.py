# From https://github.com/kubeflow/kubeflow/blob/master/kubeflow/jupyter/jupyter_config.py

import os
from importlib.util import spec_from_file_location, module_from_spec

from traitlets.config.loader import Config

K8S_SERVICE_NAME = os.environ.get('K8S_SERVICE_NAME')

# Import the UI-specific Spawner
spec = spec_from_file_location('spawner', '/etc/config/spawner.py')
spawner = module_from_spec(spec)
spec.loader.exec_module(spawner)

c: Config
######################
# JupyterHub Options #
######################
c.JupyterHub.bind_url = 'http://:8000'
c.JupyterHub.hub_bind_url = 'http://:8081'
# Don't try to cleanup servers on exit - since in general for k8s, we want
# the hub to be able to restart without losing user containers
c.JupyterHub.cleanup_servers = False

###################
# Spawner Options #
###################
c.JupyterHub.spawner_class = spawner.KubeFormSpawner
c.KubeSpawner.image = os.environ.get('NOTEBOOK_IMAGE')

c.KubeSpawner.cmd = 'start-singleuser.sh'
c.KubeSpawner.args = [
    '--allow-root',
    f'--hub-api-url=http://{K8S_SERVICE_NAME}:8081/hub/api'
]
# gpu images are very large ~15GB. need a large timeout.
c.KubeSpawner.start_timeout = 60 * 30
# Increase timeout to 5 minutes to avoid HTTP 500 errors on JupyterHub
c.KubeSpawner.http_timeout = 60 * 5

# Volume setup
c.KubeSpawner.uid = 1000
c.KubeSpawner.fs_gid = 100
c.KubeSpawner.working_dir = '/home/jovyan'
# The spawning UI allows specifying new vs existing
c.KubeSpawner.storage_pvc_ensure = False

# Set extra spawner configuration variables
c.KubeSpawner.extra_spawner_config = {
    'gcp_secret_name': None,
    'storage_class': os.environ.get('NOTEBOOK_STORAGE_CLASS'),
}

#################
# Authenticator #
#################
authenticator = os.environ.get('AUTHENTICATOR')
if authenticator == "iap":
    c.JupyterHub.authenticator_class = 'jhub_remote_user_authenticator.remote_user_auth.RemoteUserAuthenticator'
    c.RemoteUserAuthenticator.header_name = 'x-goog-authenticated-user-email'
elif authenticator == 'github':
    c.JupyterHub.authenticator_class = 'oauthenticator.github.GitHubOAuthenticator'
else:
    c.JupyterHub.authenticator_class = 'dummyauthenticator.DummyAuthenticator'
