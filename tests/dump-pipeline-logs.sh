#!/usr/bin/env bash

set -eux

pods=$(juju kubectl get pods -l workflows.argoproj.io/completed -o custom-columns=:metadata.name --no-headers)
for pod in $pods; do
    containers=$(juju kubectl get pods -o jsonpath="{.spec.containers[*].name}" $pod)

    for container in $containers; do
      juju kubectl logs --timestamps $pod -c $container
      printf '\n'
    done
    printf '\n\n'
done
