#!/usr/bin/env bash

CONTROLLER=${CONTROLLER:-cdkkf}
CLOUD=${CLOUD:-cdkkf}
MODEL=kubeflow
AWS_MODEL=${AWS_MODEL:-default}
REGION=${REGION:-us-east-1}
CHANNEL=${CHANNEL:-stable}
BUILD=${BUILD:-false}
START=$(date +%s.%N)

missing=$(for cmd in juju juju-wait kubectl $(if ${BUILD}; then echo juju-bundle; fi); do command -v $cmd > /dev/null || echo $cmd; done)
if [[ -n "$missing" ]]; then
    echo "Some dependencies were not found. Please install them with:"
    echo
    for cmd in $missing; do
        echo "    sudo snap install $cmd --classic"
    done
    echo
    exit 1
fi

# Convenience for destroying resources created by this script
case $1 in
    --destroy)
    juju destroy-controller --destroy-all-models --destroy-storage $CONTROLLER
    exit 0
    ;;
esac

export KUBECONFIG=$(mktemp /tmp/kube_config.XXXXXX)

cleanup() {
    rm $KUBECONFIG
}

trap cleanup EXIT

set -eux

# Set up Kubernetes cloud on AWS
juju bootstrap aws/$REGION $CONTROLLER
# Uncomment --overlay argument to use GPU instances
juju deploy cs:bundle/canonical-kubernetes # --overlay overlays/cdk-gpu.yml
juju deploy cs:~containers/aws-integrator
juju trust aws-integrator
juju add-relation aws-integrator kubernetes-master
juju add-relation aws-integrator kubernetes-worker

# Wait for cloud to finish booting up
juju wait -e $CONTROLLER:$AWS_MODEL -vw

juju expose kubeapi-load-balancer

# Copy details of cloud locally, and tell juju about it
juju scp -m $AWS_MODEL kubernetes-master/0:~/config $KUBECONFIG

juju add-k8s $CLOUD -c $CONTROLLER --region=ec2/$REGION --storage juju-operator-storage
juju add-model $MODEL $CLOUD

# Set up some storage for the new cloud, deploy Kubeflow, and wait for
# Kubeflow to boot up
kubectl --kubeconfig=$KUBECONFIG create -f storage/aws-ebs.yml
juju create-storage-pool k8s-ebs kubernetes storage-class=juju-ebs storage-provisioner=kubernetes.io/aws-ebs parameters.type=gp2

# Allow building local bundle.yaml, otherwise deploy from the charm store
if [[ "$BUILD" = true ]] ; then
    juju bundle deploy --build
else
    juju deploy kubeflow --channel $CHANNEL
fi

juju wait -e $CONTROLLER:$MODEL -vw

# General Kubernetes setup
find charms/*/files/sa.yaml | xargs -I[] kubectl --kubeconfig=$KUBECONFIG create -n $MODEL -f []
find charms/*/files/secret.yaml | xargs -I[] kubectl --kubeconfig=$KUBECONFIG create -n $MODEL -f []
kubectl --kubeconfig=$KUBECONFIG patch sc juju-operator-storage -p "$(<storage/is-default.yaml)"

# Expose the Ambassador reverse proxy and print out a success message
PUB_IP=$(juju status -m $AWS_MODEL | grep "kubernetes-worker/0" | awk '{print $5}')
PUB_ADDR="${PUB_IP}.xip.io"

juju config ambassador juju-external-hostname=$PUB_ADDR
juju expose ambassador

set +x

END=$(date +%s.%N)
DT=$(echo "($END - $START)/1" | bc)
DASHBOARD=$(grep -Po "server: \K(.*)" $KUBECONFIG)
USERNAME=$(grep username $KUBECONFIG)
PASSWORD=$(grep password $KUBECONFIG)

cat << EOF


Congratulations, Kubeflow is now available at ${PUB_ADDR}. Took ${DT} seconds.

The Kubernetes dashboard is available at:

    ${DASHBOARD}/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/#!/overview?namespace=${MODEL}

The username and password are:

${USERNAME}
${PASSWORD}

The central dashboard is available at http://${PUB_ADDR}/

To tear down Kubeflow and associated infrastructure, run this command:

    juju kill-controller $CONTROLLER

For more information, see documentation at:

https://github.com/juju-solutions/bundle-kubeflow/blob/master/README.md

EOF
