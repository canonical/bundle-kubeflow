# Kubeflow Operators

## Introduction

Charmed Kubeflow is a full set of Kubernetes operators to deliver the 30+ applications and services
that make up the latest version of Kubeflow, for easy operations anywhere, from workstations to
on-prem, to public cloud and edge.

A charm is a software package that includes an operator together with metadata that supports the
integration of many operators in a coherent aggregated system.

This technology leverages the Juju Operator Lifecycle Manager to provide day-0 to day-2 operations
of Kubeflow.

Visit [charmed-kubeflow.io][charmedkf] for more information.

## Install

For any Kubernetes, follow the [installation instructions][install].

## Testing

To deploy this bundle and run tests locally, do the following:

1. Set up Kubernetes, Juju, and deploy Charmed Kubeflow bundle using the [installation guide](https://charmed-kubeflow.io/docs/install).

2. Run the Automated User Acceptance Tests following the [instructions in the README file](https://github.com/canonical/charmed-kubeflow-uats#run-the-tests).

## Documentation

Read the [official documentation][docs].

[charmedkf]: https://charmed-kubeflow.io
[docs]: https://charmed-kubeflow.io/docs
[install]: https://charmed-kubeflow.io/docs/install
