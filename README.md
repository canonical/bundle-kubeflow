# KubeFlow Bundle

## Overview

This bundle deploys KubeFlow to a Juju K8s model. The individual charms that
make up this bundle can be found under `charms/`.

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

You'll also need to install the `kubectl` snap:

    sudo snap install kubectl --classic

You will then need to create an AWS account for juju to use, and then
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

### Main Dashboard

Most interactions will go through the central dashboard, which is available via
Ambassador at `/`. The deploy scripts will print out the address you can point
your browser to when they are done deploying.

### Argo UI

You can view pipelines from the Pipeline Dashboard available on the central
dashboard, or by going to `/argo/`.

### TensorFlow Jobs

To submit a TensorFlow job to the dashboard, you can run this `kubectl`
command:

    kubectl create -n <NAMESPACE> -f path/to/job/definition.yaml

Where `<NAMESPACE>` matches the name of the Juju model that you're using,
and `path/to/job/definition.yaml` should point to a `TFJob` definition
similar to the `mnist.yaml` example [found here][mnist-example].

[mnist-example]: charms/tf-job-operator/files/mnist.yaml

### TensorFlow Serving

You can submit a model to be served with TensorFlow Serving:

    # For a single model
    juju deploy cs:~kubeflow-charmers/kubeflow-tf-serving --storage models=storage-class,, --config model=/path/to/base/dir/model-name

    # For a model.conf:
    juju deploy cs:~kubeflow-charmers/kubeflow-tf-serving --storage models=storage-class,, --config model-conf=/path/to/model.conf

