# Testing Knative in airgapped

This directory is dedicated to testing Knative in an airgapped environment.

## The `helloworld` Knative Service example
The example used for testing is the `helloworld.yaml` Knative Service.

The `knative/helloworld-go` image will be included in your airgapped environment given that you used the [Airgapped test scripts](../README.md). It's specifically added in the [`get-all-images.sh` script](../../../scripts/airgapped/get-all-images.sh).

## How to test Knative in an Airgapped environment
1. Prepare the airgapped environment and Deploy CKF by following the steps in [Airgapped test scripts](../README.md).
2. Connect to the dashboard by visiting the IP of your airgapped VM. To get the IP run:
```
lxc ls | grep eth0
```
3. Log in to the dashboard and create a Profile.
4. Apply the `helloworld.yaml` found in this directory to your Profile's Namespace:
```
kubectl apply -f ./helloworld.yaml -n <your namespace>
```
5. Wait for the Knative Service to be `Ready`
```
kubectl get ksvc -n <your namespace>
```
Expected output:
```
NAME         URL                                           LATESTCREATED      LATESTREADY        READY   REASON
helloworld   http://helloworld.admin.10.64.140.43.nip.io   helloworld-00001   helloworld-00001   True    
```
6. Curl the Knative Service using the `URL` from the previous step
```
curl -L http://helloworld.admin.10.64.140.43.nip.io
```
Expected output:
```
Hello World!
```