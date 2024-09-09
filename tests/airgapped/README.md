# Testing Airgapped Installation
The scripts for testing an airgapped installation have the following requirements for the host machine:
- Internet connection
- Ubuntu 22.04
- Python 3.10
- 400 GB of disk space available

Additionally, the host machine will use Docker the pull all the images needed, and LXC to create the airgapped container.

## Update testing images

The scripts that setup and test the airgapped environment will also need to load
a list of predefined images, for running tests in the airgapped environment.

Every release has its own set of images. If you are creating a new release, you'll
need to create a new directory and the corresponding images file.

You can find such files under `tests/airgapped/<release>/testing-images.txt`

To understand how those image are being used by the tests, please take a look
at the
[Test Charmed Kubeflow components in airgapped](#test-charmed-kubeflow-components-in-airgapped)

## Setup the environment

This repository contains a script for setting up the environment:
```bash
./tests/airgapped/setup/setup.sh
```

Make sure to reboot your machine after running the setup scripts to be able to run docker commands and the lxc container to, initially, have network access.

## Prepare the airgapped cluster

You can run the script that will spin up an airgapped microk8s cluster with:

```bash
./tests/airgapped/airgap.sh \
  --node-name airgapped-microk8s \
  --microk8s-channel 1.29-strict/stable \
  --bundle-path releases/1.9/stable/bundle.yaml \
  --testing-images-path tests/airgapped/1.9/ckf-1.9-testing-images.txt \
  --juju-channel 3.4/stable
```

### Size considerations

The total size of all OCI images needed for Kubeflow is around 100 GB. As a result, the total amount of storage needed for the airgapped test is:
- 100 GB, for the host to pull all images locally.
- 100 GB, for the compressed `images.tar.gz` (the size almost always will be smaller, so this is the worst case scenario).
- 100 GB, to copy `images.tar.gz` inside the airgapped LXC machine.
- 100 GB, to copy the contents of the tarball into the container registry inside the airgapped LXC machine.

So in the worst case, 400 GB are needed to be able to run those
scripts and use all images of Kubeflow.

### Running with a subset of images

By default, if no `images.tar.gz` file is found in the working directory from where
the script was executed from, then the script will try to download
all the CKF images. These are 100 GB, which will make it difficult for running a
lot of tests locally.

Developers are urged to instead define their own `images.txt` file with the images
they'd like to be loaded during tests.

```bash
python3 scripts/airgapped/get-all-images.py \
    releases/1.9/stable/bundle.yaml \
    > images-all.txt
```

This will generate an `images-all.txt`, with all images of CKF 1.9. You can
create a copy of that file `images.txt` and keep which images you want from
the initial file, or change the rest. Then you can continue with the following
commands to generate the `images.tar.gz`:

```bash
python3 scripts/airgapped/save-images-to-cache.py images.txt
python3 scripts/airgapped/retag-images-to-cache.py images.txt
python3 scripts/airgapped/save-images-to-tar.py retagged-images.txt
```


### Common bugs

#### No internet in the LXC container when starting

This is most probably happening because LXC and Docker do not play nice together.

To mitigate try to run the following script:
```bash
./tests/airgapped/setup/lxd-docker-networking.sh
```
If the problem persists, reboot the machine and try again.


#### This "instances" entry already exists
```
Creating airgapped-microk8s
Error: Failed instance creation: Failed creating instance record: Add instance info to the database: This "instances" entry already exists
Error: Instance is not running
```

The reason for this is that the previous LXC Container still exists. To verify run `lxc ls`, where you should see `airgapped-microk8s`

**Solution**
```
lxc delete airgapped-microk8s --force
```

#### Charms are not the ones I expected

Keep in mind that the script will NOT re-fetch the charms if it finds a
`charms.tar.gz` file in the repo. This means that follow-up runs will use
that cached file.

If you want to use Charms from a different bundle, then make sure to remove
`charms.tar.gz`

## Deploy the bundle
The repository contains a scripts for deploying CKF 1.9 in airgapped:
```bash
bash ./scripts/airgapped/deploy-1.9.sh
```

If you want to deploy CKF 1.8, you can use the following script:
```bash
bash ./scripts/airgapped/deploy-1.8.sh
```

## Configure authentication and authorization
Configure the username and password to be able to log in from the dashboard
```
juju config dex-auth static-username=admin
juju config dex-auth static-password=admin
```

## Test Charmed Kubeflow components in airgapped

To test Charmed Kubeflow components in airgapped, go the directory corresponding to your Charmed Kubeflow version and follow the instructions in the READMEs.

For Charmed Kubeflow 1.9:
* [Katib](./1.9/katib/README.md)
* [KNative](./1.9/knative/README.md)
* [Pipelines](./1.9/pipelines/README.md)
* [Training Operator](./1.9/training/README.md)

For Charmed Kubeflow 1.8:
* [Katib](./1.8/katib/README.md)
* [KNative](./1.8/knative/README.md)
* [Pipelines](./1.8/pipelines/README.md)
* [Training Operator](./1.8/training/README.md)

Make sure to follow the first part of this guide on updating the OCI images that need to be present
in the airgapped cluster in order to execute tests.
