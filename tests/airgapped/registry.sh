#!/usr/bin/env bash


function setup_docker_registry() {
  local NAME=$1

  lxc exec "$NAME" -- bash -c "
    docker run -d \
      -p 5000:5000 \
      --restart=always \
      --name registry \
      -v /mnt/registry:/var/lib/registry \
      registry:2.8.1

    echo '{
    \"insecure-registries\" : [\"172.17.0.2:5000\"]
}
    ' > /etc/docker/daemon.json

    systemctl restart docker
  "
}


function push_juju_images_to_registry() {
  local NAME=$1

  lxc exec "$NAME" -- bash -c "
    microk8s ctr images pull docker.io/jujusolutions/charm-base:ubuntu-20.04
    microk8s ctr images pull docker.io/jujusolutions/charm-base:ubuntu-22.04
  "
}


function push_images_tar_to_registry() {
  local NAME=$1

  lxc exec "$NAME" -- bash -c "
    echo \"Extracting images from tar\"
    mkdir images
    tar -xzvf images.tar.gz --directory images
    rm images.tar.gz

    echo \"Loading images into intermediate Docker client\"
    for img in images/*.tar; do docker load < \$img && rm \$img; done
    rmdir images

    echo \"Pushing images from local docker to Registry\"
    python3 scripts/airgapped/push-images-to-registry.py retagged-images.txt

  "

  echo "Pushing base charm images to registry"
  push_juju_images_to_registry "$NAME"
}


function configure_to_use_registry_mirror() {
  local NAME=$1

  lxc exec "$NAME" -- bash -c '
  mkdir -p /var/snap/microk8s/current/args/certs.d/172.17.0.2:5000/

  echo "
[host.\"http://172.17.0.2:5000\"]
  capabilities = [\"pull\", \"resolve\"]
  " > /var/snap/microk8s/current/args/certs.d/172.17.0.2:5000/hosts.toml
  '
}
