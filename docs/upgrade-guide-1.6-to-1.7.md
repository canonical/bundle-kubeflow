
# How to upgrade Kubeflow from 1.6 to 1.7

Version 1.7 of Kubeflow was released in March 2023, together with the bundle and charms of Charmed Kubeflow.
To upgarde existing 1.6 Kubeflow deployment each individual charm needs to be refreshed using `juju refresh` command. In addition, some special steps need to be taken to upgrade Istio, backup data, deploy new features, and ensure existing default profile stays intact.

**Prerequisites**

- Access to dashboard of exising Charmed Kubeflow 1.6 deployment.
- Access to Kubernetes cluster where existing Charmed Kubeflow 1.6 is deployed.
- Tools: `kubectl`, `juju`

**Contents:**

- [Before upgrade](#before-upgrade)
  - [Update default 'admin' profile to prevent its deletion](Update-default-admin-profile-to-prevent-its-deletion)
- [Upgrade Istio](#upgrade-istio)
- [Upgrade charms](#upgrade-charms)
- [Deploy KNative charms](#deploy-knative-charms)
- [Verify upgrade](#verify-upgrade)


## Before upgrade

**WARNING: To prevent catastrophic data loss all important data should be backed up according to the policies of your organization.**

Before upgrading Charmed Kubeflow it is recommened to do the following:

- Stop all Notebooks.
- Review any important data that needs to be backed up and preform backup procedures according to the policies of your organization.

All upgrade steps should be done in `kubeflow` model. Before performing the upgrade switch to `kubeflow` model:



```python
juju switch kubeflow
```

### Update default 'admin' profile to prevent its deletion

In Charmed Kubeflow 1.6 a special default profile named 'admin' is created at deployment time. When upgrading to 1.7 this default profile needs to be updated in order to prevent its deletion.

Follow the folowing steps prior to upgarde to preserved default 'admin' profile.



```python
kubectl annotate profile admin controller.juju.is/id-
kubectl annotate profile admin model.juju.is/id-
kubectl label profile admin app.juju.is/created-by-
kubectl label profile admin app.kubernetes.io/managed-by-
kubectl label profile admin app.kubernetes.io/name-
kubectl label profile admin model.juju.is/name-
```

## Upgrade Istio

Upgrade of Istio service mesh components is performed according to Istio instructions and invloves upgrading charms in sequence. Note that `istio-gateway` charm should always me removed before starting upgrade. For more details on Istio upgrade and how to debug failed upgardes refere to [this document](https://github.com/canonical/istio-operators/blob/main/charms/istio-pilot/README.md)

1. Remove `istio-ingressgaeway` application and ensure it is removed successfully:


```python
juju remove-application istio-ingressgateway
```

2. Ensure that all related resources of `isiot-ingressgateway` are properly removed. The following command should succeed (return `0`)


```python
kubectl -n kubeflow get deploy istio-ingressgateway-workload 2> >(grep -q "NotFound" && echo $?)
```

3. Upgrade `istio-pilot` charm in sequence. Wait for each `refresh` command to finish and upgrade to intermediate version is complete:


```python

juju refresh istio-pilot --channel 1.12/stable
juju refresh istio-pilot --channel 1.13/stable
juju refresh istio-pilot --channel 1.14/stable
juju refresh istio-pilot --channel 1.15/stable
juju refresh istio-pilot --channel 1.16/stable

```

4. Deploy `istio-ingressgateway` add relation between `istio-pilot` and `istio-gateway`:


```python
juju deploy istio-gateway --channel 1.16/stable --trust --config kind=ingress istio-ingressgateway
juju relate istio-pilot istio-ingressgateway
```

## Upgrade charms

To upgarde Charmed Kubeflow each charm needs to be refreshed:



```python
juju refresh admission-webhook --channel latest/stable
juju refresh argo-controller --channel latest/stable
juju refresh argo-server --channel latest/stable
juju refresh dex-auth --channel latest/stable
juju refresh jupyter-controller --channel latest/stable
juju refresh jupyter-ui --channel latest/stable
juju refresh katib-controller --channel latest/stable
juju refresh katib-db --channel latest/stable
juju refresh katib-db-manager --channel latest/stable
juju refresh katib-ui --channel latest/stable
juju refresh kfp-api --channel latest/stable
juju refresh kfp-db --channel latest/stable
juju refresh kfp-persistence --channel latest/stable
juju refresh kfp-profile-controller --channel latest/stable
juju refresh kfp-schedwf --channel latest/stable
juju refresh kfp-ui --channel latest/stable
juju refresh kfp-viewer --channel latest/stable
juju refresh kfp-viz --channel latest/stable
juju refresh kubeflow-dashboard --channel latest/stable
juju refresh kubeflow-profiles --channel latest/stable
juju refresh kubeflow-roles --channel latest/stable
juju refresh kubeflow-volumes --channel latest/stable
juju refresh metacontroller-operator --channel latest/stable
juju refresh minio --channel latest/stable
juju refresh oidc-gatekeeper --channel latest/stable
juju refresh seldon-controller-manager --channel latest/stable
juju refresh tensorboard-controller --channel latest/stable
juju refresh tensorboards-web-app --channel latest/stable
juju refresh training-operator --channel latest/stable
```

## Deploy KNative charms

KNative is new addition to Charmed Kubeflow 1.7 and need to be deployed separately:

BELOW IS NOT WORKING, channels are wrong???????????????????


```python
juju deploy knative-operator --trust --channel latest/stable
juju deploy knative-serving --config namespace="knative-serving" --config istio.gateway.namespace=kubeflow --config istio.gateway.name=ingressgateway --channel latest/stable --trust
juju deploy knative-eventing --config namespace="knative-eventing" --channel latest/stable --trust
```

## Verify upgrade

You can control the progress of the update by running, when all services are in `active`/`idle` state then upgrade should be finished.


```python
watch -c juju status --color
```
