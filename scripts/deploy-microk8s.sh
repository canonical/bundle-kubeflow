#!/usr/bin/env bash

CONTROLLER=microk8s-controller
CLOUD=microk8s-cloud
MODEL=microk8s-model
START=$(date +%s.%N)

# Convenience for destroying resources created by this script
case $1 in
    --destroy)
    # Clean up resources. Kill the controller with both `kill-controller`
    # and `unregister` since edge doesn't support deleting k8s-bootstrapped
    # controllers yet.
    juju kill-controller $CONTROLLER
    microk8s.kubectl delete ns controller-$CONTROLLER
    juju unregister $CONTROLLER
    microk8s.kubectl delete ns $MODEL
    juju remove-cloud $CLOUD
    exit 0
    ;;
esac

set -eux

# Set up juju and microk8s to play nicely together
sudo microk8s.enable dns storage dashboard
microk8s.config | juju add-k8s $CLOUD
juju bootstrap $CLOUD $CONTROLLER
juju add-model $MODEL $CLOUD
# Uncomment this line to present local disks into microk8s as Persistent Volumes
# microk8s.kubectl create -f storage/local-storage.yml || true
juju create-storage-pool operator-storage kubernetes storage-class=microk8s-hostpath
juju deploy kubeflow
juju wait -w

juju config kubeflow-ambassador juju-external-hostname=localhost
juju expose kubeflow-ambassador

AMBASSADOR_IP=$(juju status | grep "kubeflow-ambassador " | awk '{print $8}')

END=$(date +%s.%N)
DT=$(echo "($END - $START)/1" | bc)
cat << EOF


Congratulations, Kubeflow is now available. Took ${DT} seconds.

Run \`microk8s.kubectl proxy\` to be able to access the dashboard at

    http://localhost:8001/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/#!/overview?namespace=$MODEL

The JupyterHub dashboard is available at http://${AMBASSADOR_IP}/hub/
The TF Jobs dashboard is available at http://${AMBASSADOR_IP}/tfjobs/ui/

To tear down Kubeflow and associated infrastructure, run this command:

    juju kill-controller $CONTROLLER

For more information, see documentation at:

https://github.com/juju-solutions/bundle-kubeflow/blob/master/README.md

EOF