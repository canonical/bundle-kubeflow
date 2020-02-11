#!/usr/bin/env bash

# Forwards ports directly to pipelines-api to avoid Ambassador auth,
# and submits pipelines to test Kubeflow.

# Kill port forwarding at script end
trap 'pkill -f svc/pipelines-api' SIGINT SIGTERM EXIT

set -eux

# Create connection directly to pipelines api, to get around ambassador auth
juju kubectl port-forward svc/pipelines-api 8888:8888 &

# Wait for port forwarding to spin up
(i=10; while ! curl localhost:8888 ; do ((--i)) || exit; sleep 1; done)

# Run tests
pytest -vvs "$@"
