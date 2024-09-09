#!/usr/bin/env bash

# This is the driver script for:
# 1. Pulling all the images/charms in host env
# 2. Create an airgapped lxd VM and install MicroK8s in it
# 3. Setup a registry mirror in that VM
#
# The script is also made to use some "caching". Specifically, if a charms.tar.gz
# or an images.tar.gz file is present then it won't regenerate them, to save time.
set -e

source tests/airgapped/utils.sh
source tests/airgapped/ckf.sh
source tests/airgapped/registry.sh


function wait_all_pods() {
  container="$1"

  echo "Waiting for all pods to start"
  lxc exec "$container" -- bash -c "
    sudo microk8s kubectl wait --for=condition=Ready pods --all --all-namespaces
  "

  echo "All pods are ready"
}

function airgap_wait_for_pods() {
  container="$1"

  lxc exec "$container" -- bash -c "
    while ! sudo microk8s kubectl wait -n kube-system ds/calico-node --for=jsonpath='{.status.numberReady}'=1; do
      echo waiting for calico
      sleep 3
    done

    while ! sudo microk8s kubectl wait -n kube-system deploy/hostpath-provisioner --for=jsonpath='{.status.readyReplicas}'=1; do
      echo waiting for hostpath provisioner
      sleep 3
    done

    while ! sudo microk8s kubectl wait -n kube-system deploy/coredns --for=jsonpath='{.status.readyReplicas}'=1; do
      echo waiting for coredns
      sleep 3
    done
  "
}

function make_machine_airgapped() {
  local NAME=$1

  lxc exec "$NAME" -- bash -c "
    ip route delete default
    ip route add default dev eth0
  "
  if lxc exec "$NAME" -- bash -c "ping -c1 1.1.1.1"; then
    echo "machine for airgap test has internet access when it should not"
    exit 1
  fi
}




function setup_microk8s() {
  local NAME=$1
  local DISTRO=$2
  local MICROK8S_CHANNEL=$3

  create_machine "$NAME" "$DISTRO"

  lxc exec "$NAME" -- snap install microk8s --classic --channel="$MICROK8S_CHANNEL"

  lxc exec "$NAME" -- bash -c "
    sudo microk8s status --wait-ready --timeout=600
    sudo microk8s enable dns:\$(resolvectl status | grep 'Current DNS Server' | awk '{print \$NF}')
    sudo microk8s enable ingress hostpath-storage metallb:10.64.140.43-10.64.140.49
  "

  echo "Wait for MicroK8s to come up"
  airgap_wait_for_pods "$NAME"
}

function create_ingress_object_in_kubeflow_namespace() {
  local NAME=$1
  if ! lxc exec "$NAME" -- bash -c 'cat <<EOF | microk8s kubectl apply -n kubeflow -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: http-ingress
  namespace: kubeflow
spec:
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            # Name must match the Service in [istio-gateway manifests](https://github.com/canonical/istio-operators/blob/track/1.17/charms/istio-gateway/src/manifest.yaml#L296)
            name: istio-ingressgateway-workload
            port:
              number: 80
EOF'; then
    echo "Error: Failed to create Ingress object in Kubeflow namespace"
    return 1
  fi
}

function post_airgap_tests() {
  local AIRGAPPED_NAME=$2
  lxc rm "$AIRGAPPED_NAME" --force
}

TEMP=$(getopt -o "lh" \
              --long help,lib-mode,registry-name:,node-name:,distro:,microk8s-channel:,juju-channel:,bundle-path:,testing-images-path:,proxy: \
              -n "$(basename "$0")" -- "$@")

if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi

eval set -- "$TEMP"

AIRGAPPED_NAME="${AIRGAPPED_NAME:-"airgapped-microk8s"}"
DISTRO="${DISTRO:-"ubuntu:22.04"}"
MICROK8S_CHANNEL="${MICROK8S_CHANNEL:-}"
JUJU_CHANNEL="${JUJU_CHANNEL:-"3.4/stable"}"
BUNDLE_PATH="${BUNDLE_PATH:-"releases/1.9/stable/bundle.yaml"}"
TESTING_IMAGES_PATH="${TESTING_IMAGES_PATH:-"tests/airgapped/1.9/testing-images.txt"}"
LIBRARY_MODE=false

while true; do
  case "$1" in
    -l | --lib-mode ) LIBRARY_MODE=true; shift ;;
    --node-name ) AIRGAPPED_NAME="$2"; shift 2 ;;
    --distro ) DISTRO="$2"; shift 2 ;;
    --microk8s-channel ) MICROK8S_CHANNEL="$2"; shift 2 ;;
    --juju-channel) JUJU_CHANNEL="$2"; shift 2 ;;
    --bundle-path) BUNDLE_PATH="$2"; shift 2 ;;
    --testing-images-path) TESTING_IMAGES_PATH="$2"; shift 2 ;;
    -h | --help )
      prog=$(basename -s.wrapper "$0")
      echo "Usage: $prog [options...]"
      echo "     --node-name <name> Name to be used for LXD containers"
      echo "         Can also be set by using AIRGAPPED_NAME environment variable"
      echo "     --distro <distro> Distro image to be used for LXD containers Eg. ubuntu:20.04"
      echo "         Can also be set by using DISTRO environment variable"
      echo "     --microk8s-channel <channel> Channel to be tested Eg. latest/edge"
      echo "         Can also be set by using MICROK8S_CHANNEL environment variable"
      echo "     --bundle-path <path> Bundle yaml to be tested"
      echo "         Can also be set by using BUNDLE_PATH environment variable"
      echo " -l, --lib-mode Make the script act like a library Eg. true / false"
      echo
      exit ;;
    -- ) shift; break ;;
    * ) break ;;
  esac
done

if [ "$LIBRARY_MODE" == "false" ];
then
  echo "1/X -- (us) Create images tar.gz"
  create_images_tar "$BUNDLE_PATH" "$TESTING_IMAGES_PATH"
  echo "2/X -- (us) Create charms tar.gz"
  create_charms_tar "$BUNDLE_PATH"
  echo "3/X -- (client) Setup K8s cluster (MicroK8s)"
  setup_microk8s "$AIRGAPPED_NAME" "$DISTRO" "$MICROK8S_CHANNEL"
  echo "4/X -- (client) Setup Docker registry, reachable from K8s cluster"
  setup_docker_registry "$AIRGAPPED_NAME"
  echo "5/X -- (field) Copy our tars to client env"
  copy_tars_to_airgapped_env "$AIRGAPPED_NAME"
  echo "6/X -- (client) Injest images from tar to their registry"
  push_images_tar_to_registry "$AIRGAPPED_NAME"
  echo "7/X -- (client) Configure access to mirror registry"
  configure_to_use_registry_mirror "$AIRGAPPED_NAME"
  echo "8/X -- Install Juju CLI and init Kubeflow model"
  install_juju "$AIRGAPPED_NAME" "$JUJU_CHANNEL"
  echo "9/X -- Make MicroK8s airgapped"
  wait_all_pods "$AIRGAPPED_NAME"
  make_machine_airgapped "$AIRGAPPED_NAME"
  echo "10/X -- Initialize Kubeflow model in JuJu"
  init_juju_model "$AIRGAPPED_NAME" "$JUJU_CHANNEL"
  echo "11/X -- Create Ingress in Kubeflow namespace"
  create_ingress_object_in_kubeflow_namespace "$AIRGAPPED_NAME"

  #echo "Cleaning up"

  lxc exec "$AIRGAPPED_NAME" -- bash -c "bash"
fi
