#!/usr/bin/env bash

function create_images_tar() {
  local BUNDLE_PATH=$1

  if [ -f "images.tar.gz" ]; then
      echo "images.tar.gz exists. Will not recreate it."
      return 0
  fi

  pip3 install -r scripts/airgapped/requirements.txt

  echo "Generating list of images of Charmed Kubeflow"
  bash scripts/airgapped/get-all-images.sh "$BUNDLE_PATH" > images.txt

  echo "Using produced list to load it into our machine's docker cache"
  python3 scripts/airgapped/save-images-to-cache.py images.txt

  echo "Retagging in our machine's docker cache all the images of the list"
  python3 scripts/airgapped/retag-images-to-cache.py images.txt

  echo "Creating images.tar.gz file with all images defined in the retagged list"
  python3 scripts/airgapped/save-images-to-tar.py retagged-images.txt
}

function create_charms_tar() {
  local BUNDLE_PATH=$1

  if [ -f "charms.tar.gz" ]; then
      echo "charms.tar.gz exists. Will not recreate it."
      return 0
  fi

  python3 scripts/airgapped/save-charms-to-tar.py \
      $BUNDLE_PATH \
      --zip-all \
      --delete-afterwards
}

function copy_tars_to_airgapped_env() {
  local NAME="$1"

  echo "Pushing images.tar.gz..."
  lxc file push images.tar.gz "$NAME"/root/

  echo "Pushing charms.tar.gz..."
  lxc file push charms.tar.gz "$NAME"/root/
  lxc exec "$NAME" -- bash -c "
    mkdir charms
    tar -xzvf charms.tar.gz --directory charms
    rm charms.tar.gz
  "

  echo "Pushing retagged images list..."
  lxc file push retagged-images.txt "$NAME"/root/

  echo "Pushed all artifacts successfully."
}

function install_juju() {
  container="$1"
  juju_channel="$2"

  lxc exec "$container" -- bash -c "
    snap install juju --channel ${juju_channel} --classic
    juju bootstrap microk8s
  "

}

function init_juju_model() {
  container="$1"

  lxc exec "$container" -- bash -c "
    juju add-model kubeflow
  "
}

function fetch_ckf_charms() {
  local NAME=$1
  local BUNDLE_PATH=$2

  lxc exec "$NAME" -- bash -c "
  python3 scripts/airgapped/download_bundle_charms.py \
      releases/1.7/stable/kubeflow/bundle.yaml \
      --zip-all \
      --delete-afterwards

  mkdir charms
  mv charms.tar.gz charms/
  cd charms
  tar -xzvf charms.tar.gz
  "
}
