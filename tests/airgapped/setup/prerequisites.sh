JUJU_CHANNEL="${JUJU_CHANNEL:-2.9/stable}"

echo "Installing pip"
sudo apt update
sudo apt install python3-pip

echo "Installing Juju"
sudo snap install juju --channel=$JUJU_CHANNEL --classic
