#!/usr/bin/env bash
set -xe

cat tests/airgapped/lxd.profile | lxd init --preseed

./tests/airgapped/setup/prerequisites.sh
./scripts/airgapped/prerequisites.sh
./tests/airgapped/setup/lxd-docker-networking.sh

echo "Setup completed. Reboot your machine before running the tests for the docker commands to run without sudo."
