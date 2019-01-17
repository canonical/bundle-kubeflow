# KubeFlow Bundle

## Overview

This bundle deploys KubeFlow to a Juju k8s model.

KubeFlow consists of:

  * TensorFlow Hub, a JupyterHub for running interactive notebooks
    with TensorFlow libraries available

  * TensorFlow Dashboard, to manage TensorFlow jobs

  * TensorFlow Training, for training TensorFlow models

  * Ambassador, an API gateway for managing access to the services


Note: This bundle is currently missing Seldon, which will be added soon.

## Deploying

### microk8s

You'll need to snap install both `juju` and `microk8s`. Kubeflow
requires at least juju 2.5rc1.

    sudo snap install juju --beta --classic
    sudo snap install microk8s --edge --classic

Next, either run the commands individually from this script, or copy/paste
them into a local script and run it:

    #!/usr/bin/env bash

    NAMESPACE=test
    CLOUD=k8stest

    cleanup() {
      # Clean up resources
      microk8s.kubectl delete ns $NAMESPACE
      juju kill-controller localhost-localhost -y -t0
      juju remove-cloud $CLOUD
    }

    trap cleanup EXIT

    set -eux

    # Set up juju and microk8s to play nicely together
    sudo microk8s.enable dns storage
    juju bootstrap lxd
    microk8s.config | juju add-k8s $CLOUD
    juju add-model $NAMESPACE $CLOUD
    juju create-storage-pool operator-storage kubernetes storage-class=microk8s-hostpath

    # Deploy kubeflow to microk8s
    juju deploy cs:~juju/kubeflow

    # Exposes the Ambassador reverse proxy at http://localhost:8081/
    # The TF Jobs dashboard is available at http://localhost:8081/tfjobs/ui/
    # The JupyterHub dashboard is available at http://localhost:8081/
    # When you're done, ctrl+c will exit this script and free the created resources
    microk8s.kubectl port-forward svc/juju-kubeflow-ambassador -n $NAMESPACE 8081:80

### CDK

TODO: CDK instructions

## TensorFlow Jobs

To submit a TensorFlow job to the dashboard, you can run this `kubectl` command:

    kubectl create -n $NAMESPACE -f path/to/job/definition.yaml

Where `$NAMESPACE` matches the name of the Juju model that you're using, and
`path/to/job/definition.yaml` should point to a `TFJob` definition similar to the
`tf_job_mnist.yaml` example [found here][mnist-example].

[mnist-example]: https://github.com/kubeflow/tf-operator/tree/master/examples/v1alpha2/dist-mnist

## TensorFlow Serving

You can submit a model to be served with TensorFlow Serving. See the documentation
in the [TF Serving Charm][tf-serving] for more information.

[tf-serving]: https://github.com/juju-solutions/charm-kubeflow-tf-serving/
