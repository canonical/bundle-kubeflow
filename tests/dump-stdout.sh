#!/usr/bin/env bash

set -eux

pods=$(microk8s kubectl get pods -n kubeflow -o custom-columns=:metadata.name --no-headers)
for pod in $pods; do
    containers=$(microk8s kubectl get pods -n kubeflow -o jsonpath="{.spec.containers[*].name}" $pod || true)

    for container in $containers; do
      microk8s kubectl logs -n kubeflow --timestamps $pod -c $container > kubeflow-$pod-$container.log || true
    done
done
