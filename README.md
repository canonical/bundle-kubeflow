# KubeFlow Bundle

## Overview

This bundle deploys KubeFlow to a Juju k8s model.

KubeFlow consists of:

  * JupyterHub, for running interactive notebooks

  * TensorFlow Job Dashboard, to manage TensorFlow jobs

  * TensorFlow Training, for training TensorFlow models

  * TensorFlow Serving, for serving TensorFlow models

  * Ambassador, an API gateway for managing access to the services

And several charms that will be added soon:

  * Seldon, for deploying ML models

  * PyTorch operator, for deploying PyTorch models

## Deploying

### Setup

If you are on macOS or Windows, you will need to use an Ubuntu VM. You
can [install multipass][multipass] and access an Ubuntu VM with these
commands:

    multipass launch --name kubeflow --mem 2G
    multipass shell kubeflow

[multipass]: https://github.com/CanonicalLtd/multipass/releases

Once you have an Ubuntu environment, you'll need to install these snaps
to get started:

    sudo snap install juju --classic
    sudo snap install juju-wait --classic

### microk8s

You'll also need to install the `microk8s` snap:

    sudo snap install microk8s --classic

Next, you can run the commands in [deploy-microk8s.sh](scripts/deploy-microk8s.sh)
individually, or run the script as a whole.

### CDK

You will first need to create an AWS account for juju to use, and then
add the credentials to juju:

    $ juju add-credential aws
    Enter credential name: kubeflow-test

    Using auth-type "access-key".

    Enter access-key: <YOUR ACCESS KEY>

    Enter secret-key: <YOUR SECRET KEY>

    Credential "kubeflow-test" added locally for cloud "aws".

Next, you can run the commands in [deploy-aws.sh](scripts/deploy-aws.sh)
individually, or run the script as a whole.

## Using

### JupyterHub

JupyterHub is available at `/hub/`.

### TensorFlow Job Dashboard

The TensorFlow Job dashboard is available at `/tfjobs/ui/`.

### TensorFlow Jobs

To submit a TensorFlow job to the dashboard, you can run this `kubectl`
command:

    kubectl create -n <NAMESPACE> -f path/to/job/definition.yaml

Where `<NAMESPACE>` matches the name of the Juju model that you're using,
and `path/to/job/definition.yaml` should point to a `TFJob` definition
similar to the `tf_job_mnist.yaml` example [found here][mnist-example].

[mnist-example]: https://github.com/kubeflow/tf-operator/tree/master/examples/v1beta1/dist-mnist

### TensorFlow Serving

You can submit a model to be served with TensorFlow Serving:

    # For a single model
    juju deploy cs:~kubeflow-charmers/kubeflow-tf-serving --storage models=storage-class,, --config model=/path/to/base/dir/model-name

    # For a model.conf:
    juju deploy cs:~kubeflow-charmers/kubeflow-tf-serving --storage models=storage-class,, --config model-conf=/path/to/model.conf

