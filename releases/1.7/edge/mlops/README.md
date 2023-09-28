# MLOps bundle

## Introduction

The MLOps bundle is a full set of Kubernetes operators to deliver the 30+ applications and services that make up Kubeflow and MLFlow for easy MLOps operations.

#### Versions
* Charmed Kubeflow 1.7/edge
* Charmed MLFlow 2.1/edge

## Install

> WARNING: this bundle is not published in Charmhub, so installation relies on the bundle definition provided in this directory.

```
juju deploy ./bundle.yaml --trust
```

## Documentation

Read the official [Charmed Kubeflow][ckfdocs] and [Charmed MLFlow][mlflowdocs] documentation.

[ckfdocs]: https://charmed-kubeflow.io/docs/
[mlflowdocs]: https://documentation.ubuntu.com/charmed-mlflow/en/latest/
