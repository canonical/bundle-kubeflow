# Airgap Utility Scripts

This directory contains bash and python scripts that are useful for performing
an airgapped installation. These scripts could either be used independently
to create airgap artifacts or via our testing scripts.

We'll document some use-case scenarios here for the different scripts.

## Prerequisites
NOTE: All the commands are expected to be run from the root directory of the repo

To use the scripts in this directory you'll need to install a couple of Python
and Ubuntu packages on the host machine, driving the test (not the LXC machine
that will contain the airgapped environment).
```
pip3 install -r scripts/airgapped/requirements.txt
sudo apt install pigz
sudo snap install docker
sudo snap install yq
sudo snap install jq
```

## Get list of all images from a bundle definition

Use the following script to get the list of all OCI images used by a bundle.
This script makes the following assumptions:
1. Every charm in the bundle has a `_github_repo_name` metadata field,
   containing the repository name of the charm (the org is assumed to be
   canonical).
2. Every charm in the bundle has a `_github_repo_branch` metadata field,
   containing the branch of the source code.
3. There is a script called `tools/get_images.sh` in each repo that gathers
   the images for that repo.

For Charmed Kubeflow 1.9, run:
```bash
python3 scripts/get-all-images.py \
    --append-images=tests/airgapped/1.9/ckf-1.9-testing-images.txt \
    releases/1.9/stable/bundle.yaml \
    > images.txt
```

For Charmed Kubeflow 1.8, run:
```bash
python3 scripts/get-all-images.py \
    --append-images=tests/airgapped/1.8/ckf-1.8-testing-images.txt \
    releases/1.8/stable/kubeflow/bundle.yaml \
    > images.txt
```

## Pull images to docker cache

We have a couple of scripts that are using `docker` commands to pull images,
retag them and compress them in a final `tar.gz` file. Those scripts require
that the images are already in docker's cache. This script pull a list of images
provided by a txt file.

```bash
python3 scripts/airgapped/save-images-to-cache.py images.txt
```

## Retag images to cache

In airgap environments users push their images in their own registries. So we'll
need to rename prefixes like `docker.io` to the server that users would use.

Note that this script will produce by default a `retagged-images.txt` file,
containing the names of all re-tagged images.

```bash
python3 scripts/airgapped/retag-images-to-cache.py images.txt
```

Or if you'd like to use a different prefix, i.e. `registry.example.com`
```bash
python3 scripts/airgapped/retag-images-to-cache.py --new-registry=registry.example.com images.txt
```

## Save images to tar

Users will need to inject the OCI images in their registry in an airgap
environment. For this we'll be preparing a `tar.gz` file with all OCI images.

```bash
python3 scripts/airgapped/save-images-to-tar.py retagged-images.txt
```

## Save charms to tar

Users in an airgap env will need to deploy charms from local files. To assist this
we'll use this script to create a `tar.gz` containing all the charms referenced
in a bundle.

```bash
BUNDLE_PATH=releases/1.7/stable/kubeflow/bundle.yaml

python3 scripts/airgapped/save-charms-to-tar.py $BUNDLE_PATH
```
