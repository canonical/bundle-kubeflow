JUJU_CHANNEL="${JUJU_CHANNEL:-3.4/stable}"

echo "Installing pip"
sudo apt update
sudo apt -y install python3-pip

echo "Installing Juju"
sudo snap install juju --channel=$JUJU_CHANNEL --classic
