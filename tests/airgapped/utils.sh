#!/usr/bin/env bash

function create_machine() {
  local NAME=$1
  local DISTRO=$2
  if ! lxc profile show microk8s
  then
    lxc profile copy default microk8s
  fi
  lxc profile edit microk8s < tests/airgapped/lxc/microk8s.profile

  lxc launch -p default -p microk8s "$DISTRO" "$NAME"

  # Allow for the machine to boot and get an IP
  sleep 20
  tar cf - ./tests | lxc exec "$NAME" -- tar xvf - -C /root
  tar cf - ./scripts | lxc exec "$NAME" -- tar xvf - -C /root
  tar cf - ./releases | lxc exec "$NAME" -- tar xvf - -C /root
  DISTRO_DEPS_TMP="${DISTRO//:/_}"
  DISTRO_DEPS="${DISTRO_DEPS_TMP////-}"
  lxc exec "$NAME" -- /bin/bash "/root/tests/airgapped/lxc/install-deps/$DISTRO_DEPS"
  lxc exec "$NAME" -- pip3 install -r scripts/airgapped/requirements.txt
  lxc exec "$NAME" -- reboot
  sleep 20

  trap 'lxc delete '"${NAME}"' --force || true' EXIT
  if [ "$#" -ne 1 ]
  then
    lxc exec "$NAME" -- reboot
    sleep 20
  fi

  # inotify increase
  lxc exec "$NAME" -- sysctl fs.inotify.max_user_instances=1280
  lxc exec "$NAME" -- sysctl fs.inotify.max_user_watches=655360
}

function setup_tests() {
  DISTRO="${1-$DISTRO}"
  FROM_CHANNEL="${2-$FROM_CHANNEL}"
  TO_CHANNEL="${3-$TO_CHANNEL}"

  export DEBIAN_FRONTEND=noninteractive
  apt-get install python3-pip -y
  pip3 install -U pytest requests pyyaml sh
  apt-get install jq -y
  snap install kubectl --classic
  export ARCH=$(uname -m)
  export LXC_PROFILE="tests/airgapped/lxc/microk8s.profile"
  export BACKEND="lxc"
  export CHANNEL_TO_TEST=${TO_CHANNEL}
}
