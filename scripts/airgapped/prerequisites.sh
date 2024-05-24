#!/usr/bin/env bash
set -xe

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

echo "Installing dependencies..."
pip3 install -r $SCRIPT_DIR/requirements.txt
sudo apt update

echo "Installing Docker"
sudo snap install docker
sudo addgroup --system docker
sudo adduser $USER docker
newgrp docker
sudo snap disable docker
sudo snap enable docker

echo "Installing parsers"
sudo snap install yq
sudo snap install jq

echo "Installing pigz for compression"
sudo apt install pigz
