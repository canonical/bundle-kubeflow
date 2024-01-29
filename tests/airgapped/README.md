# Testing Airgapped Installation
> :warning: **Those scripts require at least 500Gb**: Since they download all images of Kubeflow, both in host and inside the LXC container
>
> :warning: **Those scripts require Python 3.10**

For running the tests we expect an environment that can:
1. Spin up LXC containers
2. Have Docker, to pull images

We need docker to pull all the images necessary and push them to the airgapped
lxc container.

## Setup

We've prepared some scripts for setting up the environment
```bash
./tests/airgapped/setup/setup.sh
```

We've observed that in almost all cases we needed to reboot to be able to
run docker as sudo and the lxc container to, initially, have network access.

## Running the tests

You can run the script that will spin up an airgapped microk8s cluster with:

```bash
./tests/airgapped/airgap.sh \
  --node-name airgapped-microk8s \
  --microk8s-channel 1.24/stable \
  --bundle-path releases/latest/edge/bundle.yaml
```

### Size considerations

As stated in the beginning these scripts require a lot of storage, if run with
the full set of images of Kubeflow. To better expose this, we'll take for
granted that the total of all OCI images of Kubeflow is 125Gb. Then the amount
of storage needed is:
- 125Gb, for host to pull all images locally
- 125Gb, for the compressed `images.tar.gz` (the size almost always will be
  smaller, but here I'll use the worst case scenario
- 125Gb, to copy this tarbal inside the airgapped LXC machine
- 125Gb, to copy the contents of the tarball into the container registry inside
  the airgapped LXC machine

So in the worst case, we need to have at least 500Gb to be able to run those
scripts and use all images of Kubeflow.

### Running with a subset of images

By default, if no `images.tar.gz` file is found, in working directory from where
the script was executed from, then the script will try to download
all the CKF images. These are 125Gb, which will make it difficult for running a
lot of tests locally.

Devs are urged to instead define their own `images.txt` file with the images
they'd like to be loaded during tests. Note that in the instructions below I
used `1.7/stable` until https://github.com/canonical/bundle-kubeflow/issues/679
is resolved, and we'll be able to use other bundle files.

```bash
./scripts/airgapped/get-all-images.sh releases/1.7/stable/kubeflow/bundle.yaml > images-all.txt
```

This will generate an `images-all.txt`, with all images of CKF 1.7. You can
create a copy of that file `images.txt` and keep which images you want from
the initial file, or change the rest. Then you can continue with the following
commands to generate the `images.tar.gz`

```bash
python3 scripts/airgapped/save-images-to-cache.py images.txt
python3 scripts/airgapped/retag-images-to-cache.py images.txt
python3 scripts/airgapped/save-images-to-tar.py retagged-images.txt
```


### Common bugs

#### No internet in the LXC container when starting

This is most probably happening because LXC and Docker do not play nice together.

To mitigate try to:
1. `./tests/airgapped/setup/lxd-docker-networking.sh`
2. If the problem persists, reboot the machine


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

