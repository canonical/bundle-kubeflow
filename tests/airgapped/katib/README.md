# Testing Katib in airgapped

This directory is dedicated to testing Katib in an airgapped environment.

## Prerequisites

Prepare the airgapped environment and deploy CKF by following the steps in [Airgapped test scripts](https://github.com/canonical/bundle-kubeflow/tree/main/tests/airgapped#testing-airgapped-installation).

Once you run the test scripts, the `kubeflowkatib/simple-pbt:v0.16.0` image used in the `simple-pbt` experiment will be included in your airgapped environment. It's specifically added in the [`get-all-images.sh` script](../../../scripts/airgapped/get-all-images.sh).

## How to test Katib in an Airgapped environment
1. Connect to the dashboard by visiting the IP of your airgapped VM. To get the IP run:
```
lxc ls | grep eth0
```
Look for the IP of the `airgapped-microk8s` instance.
2. Log in to the dashboard and create a Profile.
3. Go to `Experiments (AutoML)` tab from the dashboard sidebar.
4. Click `New Experiment` then `Edit and submit YAML`.
5. Paste the contents of the `simple-pbt.yaml` file found in this directory.
6. Create the Experiment, and monitor its status to check it is `Succeeded`.