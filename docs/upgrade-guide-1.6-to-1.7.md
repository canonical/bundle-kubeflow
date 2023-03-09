
# How to upgrade Kubeflow from 1.6 to 1.7

Version 1.7 of Kubeflow was release in ......, together with the bundle and charms of Charmed Kubeflow.
To upgarde existing 1.6 Kubeflowe installation each individual charm needs to be refreshed using `juju refresh` command.

**Contents:**

- [Backup data]()
- [Upgrade the charms]()


## Backup data

To prevent catastrophic data loss all important data should be backed up.

## Upgrade the charms

Before upgrading charm it is recommened to do the following:

- Stop all Notebooks.
- Stop all Tensorboards.
- Review any important data that needs to be backed up.

To upgarde Charmed Kubeflow each charm needs to be refreshed:



```python
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
juju refresh kubeflow-roles --channel latest/edge
juju refresh kubeflow-volumes --channel latest/edge
juju refresh metacontroller-operator --channel latest/edge
juju refresh minio --channel latest/edge
juju refresh oidc-gatekeeper --channel latest/edge
juju refresh seldon-controller-manager --channel latest/edge
juju refresh tensorboard-controller --channel latest/edge
juju refresh tensorboards-web-app --channel latest/edge
juju refresh training-operator --channel latest/edge
juju refresh istio-ingressgateway --channel latest/edge
juju refresh istio-pilot --channel latest/edge
# the following will delete user namespace
juju refresh kubeflow-dashboard --channel latest/edge
juju refresh kubeflow-profiles --channel latest/edge

```

You can control the progress of the update by running:


```python
watch -c juju status --color
```
