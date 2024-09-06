# Testing training operator in airgapped

This directory is dedicated to testing training operator in an airgapped environment.

## Prerequisites

Prepare the airgapped environment and deploy CKF by following the steps in [Airgapped test scripts](../../README.md#testing-airgapped-installation).

Once you run the test scripts, the `kubeflow-ci/tf-mnist-with-summaries:1.0` image used in the `tfjob-simple` training job will be included in your airgapped environment. It's specifically added in the [`get-all-images.sh` script](../../../../scripts/airgapped/get-all-images.sh).

## How to test training operator in an Airgapped environment
1. Connect to the dashboard by visiting the IP of your airgapped VM. To get the IP run:
    ```
    lxc ls | grep eth0
    ```
    Look for the IP of the `airgapped-microk8s` instance.

2. Log in to the dashboard and create a Profile.
3. Apply the `tfjob-simple.yaml` found in this directory to your Profile's Namespace:
```
microk8s.kubectl apply -f ./tfjob-simple.yaml -n <your namespace>
```
4. Wait for the tfjob to be `Succeeded`
```
microk8s.kubectl get tfjob -n <your namespace>
```
Expected output:
```
NAME           STATE       AGE
tfjob-simple   Succeeded   2m5s
```
