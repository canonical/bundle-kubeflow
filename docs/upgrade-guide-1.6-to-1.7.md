
# How to upgrade Kubeflow from 1.6 to 1.7

Version 1.7 of Kubeflow was released in March 2023, together with the bundle and charms of Charmed Kubeflow.
To upgarde existing 1.6 Kubeflow deployment each individual charm needs to be refreshed using `juju refresh` command. In addition, some special steps need to be taken to upgrade Istio, backup data, and ensure existing default profile stays intact.

**Contents:**

- [Backup data]()
- [Upgrade the charms]()


## Prerequisites

- Access to dashboard of exising Charmed Kubeflow 1.6 deployment.
- Access to Kubernetes cluster where existing Charmed Kubeflow 1.6 is deployed.
- Tools: `kubectl`, `juju`


## Before upgrade

**WARNING: To prevent catastrophic data loss all important data should be backed up according to the policies of your organization.**

Before upgrading Charmed Kubeflow it is recommened to do the following:

- Stop all Notebooks.
- Stop all Tensorboards.
- Review any important data that needs to be backed up and preform backup procedures according to the policies of your organization.


### Update default 'admin' profile to prevent its deletion

In Charmed Kubeflow 1.6 a special default profile named 'admin' is created at deployment time. When upgrading to 1.7 this default profile needs to be updated in order to prevent its deletion.

Follow the folowing steps prior to upgarde to preserved default 'admin' profile.



```python
juju switch kubeflow
kubectl annotate profile admin controller.juju.is/id-
kubectl annotate profile admin model.juju.is/id-
kubectl label profile admin app.juju.is/created-by-
kubectl label profile admin app.kubernetes.io/managed-by-
kubectl label profile admin app.kubernetes.io/name-
kubectl label profile admin model.juju.is/name-
```

### Prepare Istio for upgrade
TBD

## Upgrade Istio
TBD

## Upgrade the charms

To upgarde Charmed Kubeflow each charm needs to be refreshed:



```python
juju switch kubeflow
juju refresh admission-webhook --channel latest/edge
juju refresh argo-controller --channel latest/edge
juju refresh argo-server --channel latest/edge
juju refresh dex-auth --channel latest/edge
juju refresh jupyter-controller --channel latest/edge
juju refresh jupyter-ui --channel latest/edge
juju refresh katib-controller --channel latest/edge
juju refresh katib-db --channel latest/edge
juju refresh katib-db-manager --channel latest/edge
juju refresh katib-ui --channel latest/edge
juju refresh kfp-api --channel latest/edge
juju refresh kfp-db --channel latest/edge
juju refresh kfp-persistence --channel latest/edge
juju refresh kfp-profile-controller --channel latest/edge
juju refresh kfp-schedwf --channel latest/edge
juju refresh kfp-ui --channel latest/edge
juju refresh kfp-viewer --channel latest/edge
juju refresh kfp-viz --channel latest/edge
juju refresh kubeflow-dashboard --channel latest/edge
juju refresh kubeflow-profiles --channel latest/edge
juju refresh kubeflow-roles --channel latest/edge
juju refresh kubeflow-volumes --channel latest/edge
juju refresh metacontroller-operator --channel latest/edge
juju refresh minio --channel latest/edge
juju refresh oidc-gatekeeper --channel latest/edge
juju refresh seldon-controller-manager --channel latest/edge
juju refresh tensorboard-controller --channel latest/edge
juju refresh tensorboards-web-app --channel latest/edge
juju refresh training-operator --channel latest/edge
# special upgrade
juju refresh istio-ingressgateway --channel latest/edge
juju refresh istio-pilot --channel latest/edge

```

You can control the progress of the update by running:


```python
watch -c juju status --color
```
