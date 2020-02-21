# KubeFlow Bundle

## Overview

This bundle deploys KubeFlow to a Juju K8s model. The individual charms that
make up this bundle can be found under `charms/`.


## Deploying

### Setup

If you are on macOS or Windows, you will need to use an Ubuntu VM. You
can [install multipass][multipass] and access an Ubuntu VM with these
commands:

    multipass launch --name kubeflow --mem 16G
    multipass shell kubeflow

16G is the recommended amount of memory to apportion the VM. Less than that
may run into issues with pods not coming up properly.

[multipass]: https://github.com/CanonicalLtd/multipass/releases

Once you have an Ubuntu environment, you'll need to install these snaps
to get started:

    sudo snap install juju --classic
    sudo snap install juju-wait --classic
    sudo snap install juju-helpers --classic

Next, check out this repository locally:

    git clone https://github.com/juju-solutions/bundle-kubeflow.git
    cd bundle-kubeflow

The below commands will assume you are running them from the `bundle-kubeflow`
directory.

Then, follow the instructions from one of the subsections below to deploy
Kubeflow to either [microk8s](#setup-microk8s) or
[Charmed Kubernetes](#setup-charmed-kubernetes).

### Setup microk8s

You'll also need to install the `microk8s` snap:

    sudo snap install microk8s --classic

Next, you will need to add yourself to the `microk8s` group:

    sudo usermod -aG microk8s $USER
    newgrp microk8s

Finally, you can run these commands to set up microk8s:

    python3 scripts/cli.py microk8s setup --controller uk8s
    python3 scripts/cli.py deploy-to uk8s

The `deploy-to` command allows manually setting a public address that
is used for accessing Kubeflow on MicroK8s. In some deployment scenarios,
you may need to configure MicroK8s to use LAN DNS instead of the default
of 8.8.8.8. To do this, edit the coredns configmap with this command:

    microk8s.kubectl edit configmap -n kube-system coredns

Edit the line with `8.8.8.8 8.8.4.4` to use your local DNS, e.g.
`192.168.1.1`.


### Setup Charmed Kubernetes

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

Next, you can run these commands to set up Charmed Kubernetes:

    python3 scripts/cli.py ck setup --controller ckkf
    python3 scripts/cli.py deploy-to ckkf

## Authentication

By default, this bundle deploys Dex configured with basic login credentials.
Dex is able to user other services for authentication, such as GitHub's OAuth
service. To configure Kubeflow to use one of these other services for
authentication, check out the [Dex documentation][dex-docs]. The YAML shown in
those examples should be configured with:

    juju config dex-auth connectors="$CONNECTOR_YAML"

[dex-docs]: https://github.com/dexidp/dex/tree/master/Documentation/connectors

As an example, this is what you might use for `$CONNECTOR_YAML` if you are
deploying with support for LDAP:

```json
[{
    "id": "ldap",
    "name": "OpenLDAP",
    "type": "ldap",
    "config": {
        "bindDN": "cn=admin,dc=example,dc=org",
        "bindPW": "admin",
        "groupSearch": {
            "baseDN": "cn=admin,dc=example,dc=org",
            "filter": "",
            "groupAttr": "DN",
            "nameAttr": "cn",
            "userAttr": "DN"
        },
        "host": "ldap-service.auth.svc.cluster.local:389",
        "insecureNoSSL": true,
        "userSearch": {
            "baseDN": "cn=admin,dc=example,dc=org",
            "emailAttr": "DN",
            "filter": "",
            "idAttr": "DN",
            "nameAttr": "cn",
            "username": "cn"
        },
        "usernamePrompt": "Email Address"
    }
}]
'
```

For more thorough examples, see https://github.com/dexidp/dex/tree/master/examples
If you'd like to disable the default basic credentials, run:

    juju config dex-auth static-username='' static-password=''

## Using

### Main Dashboard

Most interactions will go through the central dashboard, which is available via
Ambassador at `/`. The deploy scripts will print out the address you can point
your browser to when they are done deploying.

### Pipelines

Pipelines are available either by the main dashboard, or from within notebooks
via the [fairing](https://github.com/kubeflow/fairing) library.

Note that until https://github.com/kubeflow/pipelines/issues/1654 is resolved,
you will have to attach volumes to any locations that output artifacts are
written to, see the `attach_output_volume` function in
`pipline-samples/sequential.py` for an example.

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


## Removing

### Kubeflow model

To remove Kubeflow from your Kubernetes cluster, first run this command to
remove Kubeflow itself:

    juju destroy-model kubeflow --destroy-storage

If you encounter errors while destroying the model, you can run this command
to force deletion:

    juju destroy-model kubeflow --yes --destroy-storage --force

Alternatively, to simply release storage instead of deleting it, run with this
flag:

    juju destroy-model kubeflow --release-storage

### Kubeflow controller

You can destroy the controller itself with this command:

    # For microk8s
    juju destroy-controller $(juju show-controller | head -n1 | sed 's/://g') --destroy-storage

