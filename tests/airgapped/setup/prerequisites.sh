JUJU_CHANNEL=2.9/stable

echo "Installing pip"
sudo apt update
sudo apt install python3-pip

echo "Installing Juju"
sudo snap install juju --channel=$JUJU_CHANNEL --classic

echo "Installing Docker"
sudo snap install docker
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
sudo snap disable docker; sudo snap enable docker

echo "Installing parsers"
sudo snap install yq
sudo snap install jq
