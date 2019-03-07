#!/usr/bin/env bash

# Convenience for destroying resources created by this script
case $1 in
    --destroy)
    juju kill-controller aws-us-east-1
    exit 0
    ;;
esac

export KUBECONFIG=$(mktemp /tmp/kube_config.XXXXXX)

cleanup() {
    rm $KUBECONFIG
}

trap cleanup EXIT

set -eux

CLOUD=aws-kf-cloud
MODEL=aws-kf-model
START=$(date +%s.%N)

# Set up Kubernetes cloud on AWS
juju bootstrap aws/us-east-1
# Uncomment --overlay argument to use GPU instances
juju deploy cs:bundle/canonical-kubernetes # --overlay overlays/cdk-gpu.yml
juju deploy cs:~containers/aws-integrator
juju trust aws-integrator
juju add-relation aws-integrator kubernetes-master
juju add-relation aws-integrator kubernetes-worker

# Wait for cloud to finish booting up
juju wait -e aws-us-east-1:default -w

juju expose kubeapi-load-balancer

# Copy details of cloud locally, and tell juju about it
juju scp -m default kubernetes-master/0:~/config $KUBECONFIG

juju add-k8s $CLOUD
juju add-model $MODEL $CLOUD

# Set up some storage for the new cloud, deploy Kubeflow, and wait for
# Kubeflow to boot up
kubectl --kubeconfig=$KUBECONFIG create -f storage/aws-ebs.yml
juju create-storage-pool operator-storage kubernetes storage-class=juju-operator-storage storage-provisioner=kubernetes.io/aws-ebs parameters.type=gp2
juju create-storage-pool k8s-ebs kubernetes storage-class=juju-ebs storage-provisioner=kubernetes.io/aws-ebs parameters.type=gp2
juju deploy ./bundle.yaml
juju wait -e aws-us-east-1:$MODEL -w

# Expose the Ambassador reverse proxy and print out a success message
PUB_IP=$(juju status | grep "kubernetes-worker/0" | awk '{print $5}')
PUB_ADDR="${PUB_IP}.xip.io"

juju config kubeflow-ambassador juju-external-hostname=$PUB_ADDR
juju expose kubeflow-ambassador

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

The JupyterHub dashboard is available at http://${PUB_ADDR}/hub/
The TF Jobs dashboard is available at http://${PUB_ADDR}/tfjobs/ui/

To tear down Kubeflow and associated infrastructure, run this command:

    juju kill-controller aws-us-east-1

For more information, see documentation at:

https://github.com/juju-solutions/bundle-kubeflow/blob/master/README.md

EOF
