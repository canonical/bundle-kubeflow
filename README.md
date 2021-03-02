# Kubeflow Operators

## Introduction

Charmed Kubeflow is the full set Kubernetes operators to deliver the 30+ applications and services that make up the latest version of Kubeflow, for easy operations anywhere, from workstations to on-prem, to public cloud and edge.

A charm is a software package that includes an operator together with metadata that supports the integration of many operators in a coherent aggregated system. The individual charms that make up Charmed Kubeflow can be found under `charms/`.

This technology leverages the Juju Operator Lifecycle Manager to provide day-0 to day-2 operations of Kubeflow. 

Visit [charmed-kubeflow.io](https://charmed-kubeflow.io/) for more.

## Install

There are two possible paths, depending on your choice of Kubernetes:

1. For any Kubernetes, follow the [installation instructions](https://charmed-kubeflow.io/docs/install).
2. On MicroK8s, you simply have to enable the [Kubeflow add-on](https://microk8s.io/docs/addon-kubeflow).

## Documentation

Read the [official documentation](https://charmed-kubeflow.io/docs/).

## Usage details

### Argo UI

You can view pipelines from the Pipeline Dashboard available on the central
dashboard, or by going to `/argo/`.

### Pipelines

Pipelines are available either by the main dashboard, or from within notebooks
via the [fairing](https://github.com/kubeflow/fairing) library.

Note that until https://github.com/kubeflow/pipelines/issues/1654 is resolved,
you will have to attach volumes to any locations that output artifacts are
written to, see the `attach_output_volume` function in
`pipline-samples/sequential.py` for an example.

### TensorFlow Jobs

To submit a TensorFlow job to the dashboard, you can run this `kubectl`
command:

    kubectl create -n <NAMESPACE> -f path/to/job/definition.yaml

Where `<NAMESPACE>` matches the name of the Juju model that you're using,
and `path/to/job/definition.yaml` should point to a `TFJob` definition
similar to the `mnist.yaml` example [found here][mnist-example].

[mnist-example]: charms/tf-job-operator/files/mnist.yaml

### TensorFlow Serving

See [Charmed TF-serving](https://github.com/juju-solutions/charm-tf-serving)


## Uninstall

Follow the [official uninstall documentation](https://charmed-kubeflow.io/docs/uninstall).

## Tests

For information on how to run the tests in this repo, see the [tests README](tests/README.md).
