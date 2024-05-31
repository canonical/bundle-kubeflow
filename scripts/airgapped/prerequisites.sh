#!/usr/bin/env bash
set -xe

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

echo "Installing dependencies..."
pip3 install -r $SCRIPT_DIR/requirements.txt
sudo apt update

# Install and Setup Docker
# we don't do `newgrp docker` here so not to open a new bash session
# so that the rest of the scripts continue to execute.
# See in the tests/airgapped README.md instructions for the docker user changes to take effect.
echo "Installing Docker"
sudo snap install docker
sudo groupadd docker
sudo usermod -aG docker $USER
sudo snap disable docker
sudo snap enable docker

echo "Installing parsers"
sudo snap install yq
sudo snap install jq

echo "Installing pigz for compression"
sudo apt install pigz
