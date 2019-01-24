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

    CLOUD=uk8s-kf-cloud
    MODEL=uk8s-kf-model

    cleanup() {
      # Clean up resources
      microk8s.kubectl delete ns $MODEL
      juju kill-controller localhost-localhost -y -t0
      juju remove-cloud $CLOUD
    }

    trap cleanup EXIT

    set -eux

    # Set up juju and microk8s to play nicely together
    sudo microk8s.enable dns storage
    juju bootstrap lxd
    microk8s.config | juju add-k8s $CLOUD
    juju add-model $MODEL $CLOUD
    juju create-storage-pool operator-storage kubernetes storage-class=microk8s-hostpath

    # Deploy kubeflow to microk8s
    juju deploy cs:~juju/kubeflow

    # Exposes the Ambassador reverse proxy at http://localhost:8081/
    # The TF Jobs dashboard is available at http://localhost:8081/tfjobs/ui/
    # The JupyterHub dashboard is available at http://localhost:8081/hub/
    # When you're done, ctrl+c will exit this script and free the created resources
    microk8s.kubectl port-forward svc/juju-kubeflow-ambassador -n $MODEL 8081:80

### CDK

You will first need to create an AWS account for juju to use, and then add the
credentials to juju:

    $ juju add-credential aws
    Enter credential name: kubeflow-test

    Using auth-type "access-key".

    Enter access-key: <YOUR ACCESS KEY>

    Enter secret-key: <YOUR SECRET KEY>

    Credential "kubeflow-test" added locally for cloud "aws".

Next, you can run the commands in this script individually, or copy it into a
local script and run the entire script.

    #!/usr/bin/env bash

    # Clean up generated resources on exit
    cleanup() {
        juju kill-controller aws-us-east-1 -y -t0
    }

    trap cleanup EXIT

    set -eux

    CLOUD=aws-kf-cloud
    MODEL=aws-kf-model

    # Set up Kubernetes cloud on AWS
    juju bootstrap aws/us-east-1

    juju deploy cs:bundle/canonical-kubernetes
    juju deploy cs:~containers/aws-integrator
    juju trust aws-integrator
    juju add-relation aws-integrator kubernetes-master
    juju add-relation aws-integrator kubernetes-worker

    # Wait for cloud to finish booting up
    juju wait -e aws-us-east-1:default -w

    # Copy details of cloud locally, and tell juju about it
    juju scp kubernetes-master/0:~/config ~/.kube/config

    juju add-k8s $CLOUD
    juju add-model $MODEL $CLOUD

    # Set up some storage for the new cloud, deploy Kubeflow, and wait for
    # Kubeflow to boot up
    juju create-storage-pool operator-storage kubernetes storage-class=juju-operator-storage storage-provisioner=kubernetes.io/aws-ebs parameters.type=gp2
    juju create-storage-pool k8s-ebs kubernetes storage-class=juju-ebs storage-provisioner=kubernetes.io/aws-ebs parameters.type=gp2

    juju deploy cs:~juju/kubeflow
    juju wait -e aws-us-east-1:$MODEL -w


    # Exposes the Ambassador reverse proxy at http://localhost:8081/
    # The TF Jobs dashboard is available at http://localhost:8081/tfjobs/ui/
    # The JupyterHub dashboard is available at http://localhost:8081/hub/
    # When you're done, ctrl+c will exit this script and free the created resources
    kubectl port-forward svc/juju-kubeflow-ambassador -n $MODEL 8081:80


## TensorFlow Jobs

To submit a TensorFlow job to the dashboard, you can run this `kubectl` command:

    kubectl create -n <NAMESPACE> -f path/to/job/definition.yaml

Where `<NAMESPACE>` matches the name of the Juju model that you're using, and
`path/to/job/definition.yaml` should point to a `TFJob` definition similar to the
`tf_job_mnist.yaml` example [found here][mnist-example].

[mnist-example]: https://github.com/kubeflow/tf-operator/tree/master/examples/v1alpha2/dist-mnist

## TensorFlow Serving

You can submit a model to be served with TensorFlow Serving. See the documentation
in the [TF Serving Charm][tf-serving] for more information.

[tf-serving]: https://github.com/juju-solutions/charm-kubeflow-tf-serving/
