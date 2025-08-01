# Kubeflow Operators
[![CharmHub Badge](https://charmhub.io/kubeflow/badge.svg)](https://charmhub.io/kubeflow)
[![Release](https://github.com/canonical/bundle-kubeflow/actions/workflows/release-bundle-to-charmhub.yaml/badge.svg)](https://github.com/canonical/bundle-kubeflow/actions/workflows/release-bundle-to-charmhub.yaml)
[![Scan Images](https://github.com/canonical/bundle-kubeflow/actions/workflows/scan-images.yaml/badge.svg)](https://github.com/canonical/bundle-kubeflow/actions/workflows/scan-images.yaml)
[![EKS Tests](https://github.com/canonical/bundle-kubeflow/actions/workflows/deploy-to-eks.yaml/badge.svg)](https://github.com/canonical/bundle-kubeflow/actions/workflows/deploy-to-eks.yaml)
[![AKS Tests](https://github.com/canonical/bundle-kubeflow/actions/workflows/deploy-to-aks.yaml/badge.svg)](https://github.com/canonical/bundle-kubeflow/actions/workflows/deploy-to-aks.yaml)

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

We also provide a full suite of automated User Acceptance Tests (UATs) for evaluating the stability of a Charmed Kubeflow deployment. You can execute the tests by following the instructions in [the tests' repository](https://github.com/canonical/charmed-kubeflow-uats).

## Documentation

Read the [official documentation][docs].

[charmedkf]: https://charmed-kubeflow.io/
[docs]: https://charmed-kubeflow.io/docs/
[install]: https://charmed-kubeflow.io/docs/install
