
# How to upgrade Kubeflow from 1.6 to 1.7

Version 1.7 of Kubeflow was released in March 2023, together with the bundle and charms of Charmed Kubeflow.
To upgrade existing 1.6 Kubeflow deployment each individual charm needs to be refreshed using `juju refresh` command. In addition, some special steps need to be taken to upgrade Istio, backup data, deploy new features, and ensure existing default profile stays intact.

**Prerequisites**

- Access to dashboard of exising Charmed Kubeflow 1.6 deployment.
- Access to Kubernetes cluster where existing Charmed Kubeflow 1.6 is deployed.
- Tools: `kubectl`, `juju`

**Contents:**

- [Before upgrade](#before-upgrade)
  - [Update default 'admin' profile to prevent its deletion](Update-default-admin-profile-to-prevent-its-deletion)
  - [Enable trust on deployed charms](#enable-trust-on-deployed-charms)
- [Upgrade Istio](#upgrade-istio)
- [Upgrade charms](#upgrade-charms)
- [Deploy KNative and KServe charms](#deploy-knative-and-kserve-charms)
- [Verify upgrade](#verify-upgrade)


## Before upgrade

**WARNING: To prevent catastrophic data loss all important data should be backed up according to the policies of your organisation.**

Before upgrading Charmed Kubeflow it is recommended to do the following:

- Stop all Notebooks.
- Review any important data that needs to be backed up and preform backup procedures according to the policies of your organisation.
- Record all version of charms in existing Charmed Kubeflow deployment.

All upgrade steps should be done in `kubeflow` model. Before performing the upgrade switch to `kubeflow` model:



```python
# switch to kubeflow model
juju switch kubeflow
```

### Update default `admin` profile to prevent its deletion

In Charmed Kubeflow 1.6 a special default profile named `admin` is created at deployment time. When upgrading to 1.7 this default profile needs to be updated in order to prevent its deletion.

Follow the folowing steps prior to upgrade to preserved default `admin` profile.



```python
# update admin profile
kubectl annotate profile admin controller.juju.is/id-
kubectl annotate profile admin model.juju.is/id-
kubectl label profile admin app.juju.is/created-by-
kubectl label profile admin app.kubernetes.io/managed-by-
kubectl label profile admin app.kubernetes.io/name-
kubectl label profile admin model.juju.is/name-
```

### Enable trust on deployed charms

Some charms in Charmed Kubeflow 1.6 require `trust` to be enabled before upgrade.


```python
# enable trust on charms
juju trust jupyter-ui --scope=cluster
juju trust katib-ui --scope=cluster
juju trust kubeflow-dashboard --scope=cluster
juju trust kubeflow-profiles --scope=cluster
juju trust seldon-controller-manager --scope=cluster
```

## Upgrade Istio

Upgrade of Istio service mesh components is performed according to Istio instructions and invloves upgrading charms in sequence. Note that `istio-gateway` charm should always me removed before starting upgrade. For more details on Istio upgrade and how to debug failed upgrades refer to [this document](https://github.com/canonical/istio-operators/blob/main/charms/istio-pilot/README.md). It is assumed that `istio-pilot` version in Charmed Kubeflow deployed is 1.11.

1. Remove `istio-ingressgaeway` application and corresponding relation with `istio-pilot`:


```python
# remove relation and istio-ingressgateway application
juju remove-relation istio-pilot istio-ingressgateway
juju remove-application istio-ingressgateway
```

2. Ensure that `istio-ingressgateway` application and all related resources are properly removed. The following commands should succeed (return `0`):


```python
juju show-application istio-ingressgateway 2> >(grep -q "not found" && echo $?)
kubectl -n kubeflow get deploy istio-ingressgateway-workload 2> >(grep -q "NotFound" && echo $?)
```

*Troubleshooting of removal of `istio-ingressgateway` application*

If required, remove `istio-ingressgateway` application with `--force` option and remove `istio-ingressgateway-workload` manually:


```python
    juju remove-application --force istio-ingressgateway
    kubectl -n kubeflow delete deploy istio-ingressgateway-workload
```

3. Upgrade `istio-pilot` charm in sequence. Wait for each `refresh` command to finish and upgrade to intermediate version is complete:


```python
# upgrade istio-pilot in sequence
juju refresh istio-pilot --channel 1.12/stable
juju refresh istio-pilot --channel 1.13/stable
juju refresh istio-pilot --channel 1.14/stable
juju refresh istio-pilot --channel 1.15/stable
juju refresh istio-pilot --channel 1.16/stable
```

*Troubleshooting of Istio upgrade*

Refer to [this document](https://github.com/canonical/istio-operators/blob/main/charms/istio-pilot/README.md) for troubleshooting tips.

4. Deploy `istio-ingressgateway` add relation between `istio-pilot` and `istio-gateway`:


```python
# deploy istio-ingressgateway
juju deploy istio-gateway --channel 1.16/stable --trust --config kind=ingress istio-ingressgateway
juju relate istio-pilot istio-ingressgateway
```

## Upgrade charms

To upgrade Charmed Kubeflow each charm needs to be refreshed. It is recommended to wait for each charm to finish its upgrade before proceeding with the next.

Depending on original deployment of Charmed Kuberflow version 1.6, refresh command will report that charm is up-to-date which indicates that there is not need to upgrade that particular charm.

During the upgrade some charms can temporarily  go into `error` or `blocked` state. 



```python
# upgrade charms
juju refresh admission-webhook --channel 1.7/stable
juju refresh argo-controller --channel 3.3/stable
juju refresh argo-server --channel 3.3/stable
juju refresh dex-auth --channel 2.31/stable
juju refresh jupyter-controller --channel 1.7/stable
juju refresh jupyter-ui --channel 1.7/stable
juju refresh katib-controller --channel 0.15/stable
juju refresh katib-db --channel latest/stable
juju refresh katib-db-manager --channel 0.15/stable
juju refresh katib-ui --channel 0.15/stable
juju refresh kfp-api --channel 2.0/stable
juju refresh kfp-db --channel latest/stable
juju refresh kfp-persistence --channel 2.0/stable
juju refresh kfp-profile-controller --channel 2.0/stable
juju refresh kfp-schedwf --channel 2.0/stable
juju refresh kfp-ui --channel 2.0/stable
juju refresh kfp-viewer --channel 2.0/stable
juju refresh kfp-viz --channel 2.0/stable
juju refresh kubeflow-dashboard --channel 1.7/stable
juju refresh kubeflow-profiles --channel 1.7/stable
juju refresh kubeflow-roles --channel 1.7/stable
juju refresh kubeflow-volumes --channel 1.7/stable
juju refresh metacontroller-operator --channel 2.0/stable
juju refresh minio --channel ckf-1.7/stable
juju refresh oidc-gatekeeper --channel ckf-1.7/stable
juju refresh seldon-controller-manager --channel 1.15/stable
juju refresh tensorboard-controller --channel 1.7/stable
juju refresh tensorboards-web-app --channel 1.7/stable
juju refresh training-operator --channel 1.6/stable
```

*Troubleshooting charm upgrade*

If charm fails upgrade or is stuck in `maintenance` state for long time it is possible to recover by running refresh command with version that was there prior to deployment, i.e. downgrade the charm.

## Deploy KNative and KServe charms

KNative and KServe are new additions to Charmed Kubeflow 1.7 and need to be deployed separately as part of the upgrade:


```python
# install knative and kserve
juju deploy knative-operator --channel 1.8/stable --trust
juju deploy knative-serving --config namespace="knative-serving" --config istio.gateway.namespace=kubeflow --config istio.gateway.name=ingressgateway --channel 1.8/stable --trust
juju deploy knative-eventing --config namespace="knative-eventing" --channel 1.8/stable --trust
juju deploy kserve-controller --channel 0.10/stable --trust
```

## Verify upgrade

You can control the progress of the update by running, when all services are in `active`/`idle` state then upgrade should be finished.


```python
watch -c juju status --color
```

All applications and units should be in `active` (green) state.
