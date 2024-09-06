# Testing Knative in airgapped

This directory is dedicated to testing Knative in an airgapped environment.

## Prerequisites

Prepare the airgapped environment and deploy CKF by following the steps in [Airgapped test scripts](https://github.com/canonical/bundle-kubeflow/tree/main/tests/airgapped#testing-airgapped-installation).

Once you run the test scripts, the `knative/helloworld-go` image used in the `helloworld` example will be included in your airgapped environment. It's specifically added in the [`get-all-images.sh` script](../../../../scripts/airgapped/get-all-images.sh).

## How to test Knative in an Airgapped environment
1. Connect to the dashboard by visiting the IP of your airgapped VM. To get the IP run:
```
lxc ls | grep eth0
```
2. Log in to the dashboard and create a Profile.
3. Apply the `helloworld.yaml` found in this directory to your Profile's Namespace:
```
microk8s kubectl apply -f ./helloworld.yaml -n <your namespace>
```
4. Wait for the Knative Service to be `Ready`
```
microk8s kubectl get ksvc -n <your namespace>
```
Expected output:
```
NAME         URL                                           LATESTCREATED      LATESTREADY        READY   REASON
helloworld   http://helloworld.admin.10.64.140.43.nip.io   helloworld-00001   helloworld-00001   True    
```
5. Curl the Knative Service using the `URL` from the previous step
```
curl -L http://helloworld.admin.10.64.140.43.nip.io
```
Expected output:
```
Hello World!
```
