cat tests/airgapped/lxd.profile | lxd init --preseed
pip3 install -r scripts/airgapped/requirements.txt

./tests/airgapped/setup/prerequisites.sh
./tests/airgapped/setup/lxd-docker-networking.sh
