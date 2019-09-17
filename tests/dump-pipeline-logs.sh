#!/usr/bin/env bash

set -eux

pods=`juju kubectl get pods -l workflows.argoproj.io/completed="true" -o custom-columns=:metadata.name --no-headers`
for pod in $pods; do
    juju kubectl logs -c main --timestamps $pod
    printf '\n'

    juju kubectl logs -c wait --timestamps $pod
    printf '\n\n'
done