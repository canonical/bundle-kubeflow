#!/usr/bin/env bash

CONTROLLER=${CONTROLLER:-uk8s}
CLOUD=${CLOUD:-microk8s}
MODEL=kubeflow
CHANNEL=${CHANNEL:-stable}
BUILD=${BUILD:-false}
START=$(date +%s.%N)
CI=${CI:-false}

missing=$(for cmd in juju juju-wait microk8s.kubectl $(if ${BUILD}; then echo juju-bundle; fi); do command -v $cmd > /dev/null || echo $cmd; done)
if [[ -n "$missing" ]]; then
    echo "Some dependencies were not found. Please install them with:"
    echo
    for cmd in $missing; do
        echo "    sudo snap install ${cmd//\.*/} --classic"
    done
    echo
    exit 1
fi

# Convenience for destroying resources created by this script
case $1 in
    --destroy)
    # Clean up resources.
    juju destroy-controller --destroy-all-models --destroy-storage $CONTROLLER
    exit 0
    ;;
esac

set -eux

# Set up juju and microk8s to play nicely together
sudo microk8s.enable dns storage dashboard

for i in {1..5}; do microk8s.status --wait-ready --timeout 60 && break || sleep 10; done

juju bootstrap $CLOUD $CONTROLLER
juju add-model $MODEL $CLOUD
# Uncomment this line to present local disks into microk8s as Persistent Volumes
# microk8s.kubectl create -f storage/local-storage.yml || true
juju create-storage-pool operator-storage kubernetes storage-class=microk8s-hostpath

# Allow building local bundle.yaml, otherwise deploy from the charm store
if [[ "$BUILD" = true ]] ; then
    juju bundle deploy --build $(if ${CI}; then echo "-- --overlay overlays/ci.yml"; fi)
else
    juju deploy kubeflow --channel $CHANNEL
fi

juju wait -vw

# General Kubernetes setup
find charms/*/files/sa.yaml | xargs -I[] bash -c "microk8s.kubectl create -n $MODEL -f [] || true"
find charms/*/files/secret.yaml | xargs -I[] bash -c "microk8s.kubectl create -n $MODEL -f [] || true"

juju config ambassador juju-external-hostname=localhost
juju expose ambassador

AMBASSADOR_IP=$(juju status | grep "ambassador " | awk '{print $8}')

END=$(date +%s.%N)
DT=$(echo "($END - $START)/1" | bc)
cat << EOF


Congratulations, Kubeflow is now available. Took ${DT} seconds.

Run \`microk8s.kubectl proxy\` to be able to access the dashboard at

    http://localhost:8001/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/#!/overview?namespace=$MODEL

The central dashboard is available at http://${AMBASSADOR_IP}/

To tear down Kubeflow and associated infrastructure, run this command:

    juju kill-controller $CONTROLLER

For more information, see documentation at:

https://github.com/juju-solutions/bundle-kubeflow/blob/master/README.md

EOF
