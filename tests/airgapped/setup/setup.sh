#!/usr/bin/env bash
set -xe

cat tests/airgapped/lxd.profile | lxd init --preseed

./tests/airgapped/setup/prerequisites.sh
./scripts/airgapped/prerequisites.sh
./tests/airgapped/setup/lxd-docker-networking.sh

pip3 install -r ./scripts/requirements.txt
sudo apt install pigz
sudo snap install docker
sudo snap install yq
sudo snap install jq

echo "Setup completed. Reboot your machine before running the tests for the docker commands to run without sudo."
