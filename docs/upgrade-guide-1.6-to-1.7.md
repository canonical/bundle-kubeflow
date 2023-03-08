
# How to upgrade Kubeflow from 1.6 to 1.7

Version 1.7 of Kubeflow was release in ......, together with the bundle and charms of Charmed Kubeflow.
To upgarde existing 1.6 Kubeflowe installation each individual charm needs to be refreshed using `juju refresh` command. For some charms additional manual procedures are required to prevent data loss and ensure proper post-upgarde behaviour.

>>> WARNING on data loss

**Contents:**

- [Remove existing relations]()
- [Backup data]()
- [Upgrade the charms]()
- [Upgrade Minio]()
  - [Minio data migration and re-deployment instructions]()

## Remove existing relations


```python
juju switch kubeflow
juju status --relations | grep regular | awk '{print $1" "$2}' | xargs -l juju remove-relation
```

## Backup data
To prevent catastrophic data loss all imporatant data should be backed up.

## Upgrade the charms

To upgarde Kubeflow each charm needs to be refreshed:


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
juju refresh oidc-gatekeeper --channel latest/edge
juju refresh seldon-controller-manager --channel latest/edge
juju refresh tensorboard-controller --channel latest/edge
juju refresh tensorboards-web-app --channel latest/edge
juju refresh training-operator --channel latest/edge
```

## Upgrade Minio

Minio charm upgrade is done through re-deployment - removing existing Minio charm and deploying updated Minio charm. As a result, this upgarde requires storage migration to be performed which is done by copying of data from existing storage to newly created storage.

### Minio data migration and re-deployment instructions

1. Store Minio credentials:


```python
MINIO_USER=$(juju config minio secret-key)
MINIO_PASSWORD=$(juju config minio secret-key)
```

2. Remove all Minio relations (if not removed in previous step):


```python
juju remove-relation minio:object-storage argo-controller:object-storage
juju remove-relation minio:object-storage kfp-api:object-storage
juju remove-relation minio:object-storage kfp-profile-controller:object-storage
juju remove-relation minio:object-storage kfp-ui:object-storage
juju remove-relation minio:object-storage mlflow-server:object-storage
```


3. Change reclaim policy of existing Minio PV and obtain exisitng PVC name and size which will be used as source of data migration:


```python
PV_NAME=$(kubectl -n kubeflow get pv | grep minio | awk '{print $1}')
kubectl patch pv $PV_NAME -p '{"spec":{"persistentVolumeReclaimPolicy":"Retain"}}'
SOURCE_PVC=$(kubectl -n kubeflow get statefulset minio -o=json | jq -r '(.spec.volumeClaimTemplates)[0].metadata.name')
PV_SIZE=?????
```

4. Remove Minio application (storage will be detached and retained):


```python
juju remove-application minio
```

5. Deploy new Minio charm with same storage size and obtain new PVC name which will be used as a destination for data migration:


```python
juju deploy minio --channel edge --storage minio-data=$PV_SIZE
DESTINATION_PVC=$(kubectl -n kubeflow get statefulset minio -o=json | jq -r '(.spec.volumeClaimTemplates)[0].metadata.name')
```

6. Re-configure Minio credentials and verify that all data can be accessed by accessing Minio dashboard:


```python
juju config minio secret-key=$MINIO_USER
juju config minio secret-key=$MINIO_PASSWORD
```

7. Create migration pod definition in `pod-minio-migration.yaml`:
```
apiVersion: v1
kind: Pod
metadata:
  name: minio-migration
  namespace: kubeflow
spec:
  containers:
  - name: minio-migration
    image: busybox
    args:
    - sleep
    - "1000000"
    volumeMounts:
      - name: source
        mountPath: /data-source
      - name: destination
        mountPath: /data-destination
  volumes:
    - name: source
      persistentVolumeClaim:
        claimName: SOURCE_PVC-minio-0
        readOnly: false
    - name: destination  
      persistentVolumeClaim:
        claimName: DESTINATION_PVC-minio-0
        readOnly: false
```

8. Start migration pod:


```python
sed "s/SOURCE_PVC/${SOURCE_PVC}/g;s/DESTINATION_PVC/${DESTINATION_PVC}/g;" pod-minio-migration.yaml | kubectl apply -f -
```

9. Ensure that `minio-migration` pod is running and execute data copy command from source PVC to destination PVC:


```python
kubectl -n kubeflow exec -ti minio-migration -- /bin/sh -c "cp -rfpT /data-source/ /data-destination/ && sync && exit"
```

10. After data copying is complete delete migration pod:


```python
kubectl -n kubeflow delete pod minio-migration
```

11. Verify that data is accessible by navigating to Minio dashboard.

12. After completed deployment with relations and additional testing of data integrity old PV and PVC can be removed:


```python
kubectl -n kubeflow delete pv $PV_NAME
kubectl -n kubeflow delete pvc $SOURCE_PVC
```

## Add relations

The charms now require relations to be added again to complete a working deployment. You do not need to wait for all the charms to be deployed to add these relations.


```python
juju relate argo-controller minio
juju relate dex-auth:oidc-client oidc-gatekeeper:oidc-client
juju relate istio-pilot:ingress dex-auth:ingress
juju relate istio-pilot:ingress jupyter-ui:ingress
juju relate istio-pilot:ingress kfp-ui:ingress
juju relate istio-pilot:ingress kubeflow-dashboard:ingress
juju relate istio-pilot:ingress kubeflow-volumes:ingress
juju relate istio-pilot:ingress oidc-gatekeeper:ingress
juju relate istio-pilot:ingress-auth oidc-gatekeeper:ingress-auth
juju relate istio-pilot:istio-pilot istio-ingressgateway:istio-pilot
juju relate kfp-api kfp-db
juju relate kfp-api:kfp-api kfp-persistence:kfp-api
juju relate kfp-api:kfp-api kfp-ui:kfp-api
juju relate kfp-api:kfp-viz kfp-viz:kfp-viz
juju relate kfp-api:object-storage minio:object-storage
juju relate kfp-profile-controller:object-storage minio:object-storage
juju relate kfp-ui:object-storage minio:object-storage
juju relate kubeflow-profiles kubeflow-dashboard
juju relate istio-pilot:ingress tensorboards-web-app:ingress
juju relate istio-pilot:gateway tensorboard-controller:gateway
juju relate istio-pilot:ingress katib-ui:ingress
juju relate katib-db-manager katib-db
```

You can control the progress of the update by running:


```python
watch -c juju status --color
```

# User namespace is wiped out
juju refresh kubeflow-dashboard --channel latest/edge
juju refresh kubeflow-profiles --channel latest/edge

# Istio is not upgrading properly
juju refresh istio-ingressgateway --channel latest/edge
juju refresh istio-pilot --channel latest/edge
