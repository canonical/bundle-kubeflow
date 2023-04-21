
# How to upgrade Charmed Kubeflow from 1.6 to 1.7

Version 1.7 of Charmed Kubeflow was released in March 2023, aligning with the upstream Kubeflow project [release](https://github.com/kubeflow/manifests/releases/tag/v1.7.0).
To upgrade existing 1.6 Kubeflow deployment each charm has to be refreshed using `juju refresh`. In addition, this guide includes steps to be taken to upgrade certain components, backup data, and deploy new features.

**Prerequisites**

- An active and idle Charmed Kubeflow 1.6 deployment. This requires all charms in the bundle to be in that state.
Access to dashboard of exising Charmed Kubeflow 1.6 deployment.
- Admin access to Kubernetes cluster where existing Charmed Kubeflow 1.6 is deployed.
- Tools: `kubectl`, `juju`

**Contents:**

- [Before upgrade](#before-charmed-kubeflow-upgrade)
- [Upgrade Istio](#upgrade-istio)
- [Before charms upgrade](#before-charms-upgrade)
  - [Update default 'admin' profile to prevent its deletion](#update-default-admin-profile-to-prevent-its-deletion)
  - [Enable trust on deployed charms](#enable-trust-on-deployed-charms)
- [Upgrade charms](#upgrade-charms)
- [Deploy KNative and KServe charms](#deploy-knative-and-kserve-charms)
- [Verify upgrade](#verify-upgrade)


## Before Charmed Kubeflow upgrade

**WARNING: To prevent data loss, all important data should be backed up according to the policies of your organisation.**

Before upgrading Charmed Kubeflow it is recommended to do the following:

- Stop all Notebooks.
- Review any important data that needs to be backed up and preform backup procedures according to the policies of your organisation.
- Record all charm versions in existing Charmed Kubeflow deployment.

All upgrade steps should be done in `kubeflow` model. If you haven't already, switch to `kubeflow` model:



```python
# switch to kubeflow model
juju switch kubeflow
```

## Upgrade Istio

Upgrade of istio components is performed according to Istio's [best practices](https://istio.io/latest/docs/setup/upgrade/), which requires upgrading Istio by one minor version at a time and in sequence. For more details on upgrading and troubleshooting `istio-pilot` and `istio-ingressgateway` charms, please refer to [this document](https://github.com/canonical/istio-operators/blob/main/charms/istio-pilot/README.md). It is assumed that the deployed `istio-pilot` and `istio-ingressgateway` version alongside Charmed Kubeflow 1.6 is 1.11.

1. Remove the `istio-ingressgateway` application and corresponding relation with `istio-pilot`:


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

<!-- This should be placed in [detail] section on Discourse -->
#### Troubleshooting of removal of `istio-ingressgateway` application

**WARNING: Removing application using `--force` option should be the last resort. There could be potential stability issues if application is not shutdown cleanly.**

If required, remove `istio-ingressgateway` application with `--force` option and remove `istio-ingressgateway-workload` manually:


```python
    juju remove-application --force istio-ingressgateway
    kubectl -n kubeflow delete deploy istio-ingressgateway-workload
```

3. Upgrade `istio-pilot` charm in sequence. Wait for each `refresh` command to finish and upgrade to intermediate version is complete, i.e. `istio-pilot` application is in `active` state and unit is in `active/idle` state:


```python
# upgrade istio-pilot from 1.11 to 1.12
juju refresh istio-pilot --channel 1.12/stable
```

Initial upgrade from 1.11 to 1.12 might take some time. Ensure that `istio-pilot` charm has completed its upgrade.


```python
# upgrade istio-pilot from 1.12 to 1.13
juju refresh istio-pilot --channel 1.13/stable
```


```python
# upgrade istio-pilot from 1.13 to 1.14
juju refresh istio-pilot --channel 1.14/stable
```


```python
# upgrade istio-pilot from 1.14 to 1.15
juju refresh istio-pilot --channel 1.15/stable
```


```python
# upgrade istio-pilot from 1.15 to 1.16
juju refresh istio-pilot --channel 1.16/stable
```

<!-- This should be placed in [detail] section on Discourse -->
#### Troubleshooting of Istio upgrade

Refer to [this document](https://github.com/canonical/istio-operators/blob/main/charms/istio-pilot/README.md) for troubleshooting tips.

4. Deploy `istio-ingressgateway` add relation between `istio-pilot` and `istio-gateway`:


```python
# deploy istio-ingressgateway
juju deploy istio-gateway --channel 1.16/stable --trust --config kind=ingress istio-ingressgateway
juju relate istio-pilot istio-ingressgateway
```

## Before charms upgrade

Before charms can be upgraded the following actions need to be taken:
- Eanble trust on deployed charms (required).
- Updayed default `admin` profile to prevent its deletion (optional)

### Enable trust on deployed charms

Because of changes in the charm code, some charms in Charmed Kubeflow 1.6 have to be trusted by juju before the upgrade.

**WARNING: Please note that if you do not execute `juju trust` for these charms, you may encounter authorization errors. If that is the case, please refer to the Troubleshooting guide.**


```python
# enable trust on charms
juju trust jupyter-ui --scope=cluster
juju trust katib-ui --scope=cluster
juju trust kubeflow-dashboard --scope=cluster
juju trust kubeflow-profiles --scope=cluster
juju trust seldon-controller-manager --scope=cluster
```

### Update default `admin` profile to prevent its deletion

In Charmed Kubeflow 1.6 a user profile named `admin` is created by default at deployment time.  This profile has no additional priviledges - it is just a default profile that was created for convenience and has been removed as of Charmed Kubeflow 1.7.  When upgrading to 1.7 this default profile will be deleted.  If you depend on this profile, you can do the following to prevent its deletion:


```python
# update admin profile
kubectl annotate profile admin controller.juju.is/id-
kubectl annotate profile admin model.juju.is/id-
kubectl label profile admin app.juju.is/created-by-
kubectl label profile admin app.kubernetes.io/managed-by-
kubectl label profile admin app.kubernetes.io/name-
kubectl label profile admin model.juju.is/name-
```

### Re-deploy `kubeflow-roles`

There is a difference how charms are handling Roles and ClusterRoles in 1.7 release. As a result, `kubeflow-roles` charm needs to be re-deployed rather than refreshed:


```python
# redeploy kubeflow-roles
juju remove-application kubeflow-roles
juju deploy kubeflow-roles --channel 1.7/stable
```

## Upgrade charms

To upgrade Charmed Kubeflow each charm needs to be refreshed. It is recommended to wait for each charm to finish its upgrade before proceeding with the next.

Depending on original deployment of Charmed Kuberflow version 1.6, refresh command will report that charm is up-to-date which indicates that there is not need to upgrade that particular charm.

During the upgrade some charms can temporarily  go into `error` or `blocked` state, but they should go `active` after a while.


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
juju refresh kubeflow-volumes --channel 1.7/stable
juju refresh metacontroller-operator --channel 2.0/stable
juju refresh minio --channel ckf-1.7/stable
juju refresh oidc-gatekeeper --channel ckf-1.7/stable
juju refresh seldon-controller-manager --channel 1.15/stable
juju refresh tensorboard-controller --channel 1.7/stable
juju refresh tensorboards-web-app --channel 1.7/stable
juju refresh training-operator --channel 1.6/stable
```

<!-- This should be placed in [detail] section on Discourse -->
#### Troubleshooting charm upgrade

If charm fails upgrade or is stuck in `maintenance` state for long time it is possible to recover by running refresh command with version that was there prior to deployment, i.e. downgrade the charm. After that repeat the upgrade.

## Deploy KNative and KServe charms

KNative and KServe are new additions to Charmed Kubeflow 1.7 and need to be deployed separately as part of the upgrade:


```python
# install knative and kserve
juju deploy knative-operator --channel 1.8/stable --trust
juju deploy knative-serving --config namespace="knative-serving" --config istio.gateway.namespace=kubeflow --config istio.gateway.name=kubeflow-gateway --channel 1.8/stable --trust
juju deploy knative-eventing --config namespace="knative-eventing" --channel 1.8/stable --trust
juju deploy kserve-controller --channel 0.10/stable --trust
```

## Verify upgrade

You can control the progress of the update by running, when all services are in `active`/`idle` state then upgrade should be finished.


```python
watch -c juju status --color
```

All applications and units should be in `active` (green) state.
