#!/usr/bin/env bash

export KUBECONFIG=$(mktemp /tmp/kube_config.XXXXXX)

cleanup() {
    rm $KUBECONFIG
}

trap cleanup EXIT

export MODEL="aws-kf-model"
juju scp -m default kubernetes-master/0:~/config $KUBECONFIG
export INSTANCE=$(kubectl --kubeconfig $KUBECONFIG -n $MODEL get pods -l $1 --no-headers -o custom-columns=":metadata.name")
kubectl --kubeconfig $KUBECONFIG exec -n $MODEL -it $INSTANCE bash
