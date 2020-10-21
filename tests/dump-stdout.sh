#!/usr/bin/env bash

set -eux

mkdir -p "$1"

pods=$(microk8s kubectl get pods -n kubeflow -o custom-columns=:metadata.name --no-headers)
for pod in $pods; do
    containers=$(microk8s kubectl get pods -n kubeflow -o jsonpath="{.spec.containers[*].name}" $pod || true)

    for container in $containers; do
      microk8s kubectl logs -n kubeflow --timestamps $pod -c $container > "$1"/kubeflow-$pod-$container.log || true
    done
done
