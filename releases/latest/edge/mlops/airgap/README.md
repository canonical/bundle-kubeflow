# MLOps bundle for airgap environments

## Introduction

The MLOps bundle is a full set of Kubernetes operators to deliver the 30+ applications and services that make up Kubeflow and MLFlow for easy MLOps operations in airgapped environments.

## Install

> WARNING: this bundle is not published in Charmhub, so installation relies on the bundle definition provided in this directory.

```
# Deploy CKF and Charmed MLFlow charms from the bundle definition
juju deploy ./bundle-airgap.yaml --trust

# Deploy an extra set of charms that complete the CKF set.
# These are not included in the bundle definition because the deployment instructions are slightly different.
./podspec_script.sh
```

## Documentation

Read the official [Charmed Kubeflow][ckfdocs] and [Charmed MLFlow][mlflowdocs] documentation.

[ckfdocs]: https://charmed-kubeflow.io/docs/
[mlflowdocs]: https://documentation.ubuntu.com/charmed-mlflow/en/latest/
