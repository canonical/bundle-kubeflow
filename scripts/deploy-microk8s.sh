#!/usr/bin/env bash

CLOUD=microk8s-cloud
MODEL=microk8s-model

# Convenience for destroying resources created by this script
case $1 in
    --destroy)
    # Clean up resources
    juju kill-controller localhost-localhost
    microk8s.kubectl delete ns $MODEL
    juju remove-cloud $CLOUD
    exit 0
    ;;
esac

set -eux

# Set up juju and microk8s to play nicely together
sudo microk8s.enable dns storage
juju bootstrap lxd
microk8s.config | juju add-k8s $CLOUD
juju add-model $MODEL $CLOUD
microk8s.kubectl create -f storage/local-storage.yml || true
juju create-storage-pool operator-storage kubernetes storage-class=microk8s-hostpath
juju deploy cs:~kubeflow-charmers/kubeflow
juju wait -w

juju config kubeflow-ambassador juju-external-hostname=localhost
juju expose kubeflow-ambassador

AMBASSADOR_IP=$(juju status | grep "kubeflow-ambassador " | awk '{print $8}')

cat << EOF


Congratulations, Kubeflow is now available. Run `microk8s.kubectl proxy` to be able to access the dashboard at

    http://localhost:8001/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/#!/overview?namespace=$MODEL

The JupyterHub dashboard is available at http://${AMBASSADOR_IP}/hub/
The TF Jobs dashboard is available at http://${AMBASSADOR_IP}/tfjobs/ui/

To tear down Kubeflow and associated infrastructure, run this command:

    juju kill-controller aws-us-east-1

For more information, see documentation at:

https://github.com/juju-solutions/bundle-kubeflow/blob/master/README.md

EOF
