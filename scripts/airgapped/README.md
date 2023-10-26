# Airgap Utility Scripts

This directory contains bash and python scripts that are useful for performing
an airgapped installation. These scripts could either be used independently
to create airgap artifacts or via our testing scripts.

We'll document some use-case scenarios here for the different scripts.

## Prerequisites

To use the scripts in this directory you'll need to install a couple of Python
and Ubuntu packages.
```
pip3 install -r requirements.txt
sudo apt install pigz
```

## Get list of all images in bundle

In a lot of cases we need to have the list of all OCI Images used by a bundle.
To get this list we can use the following script. This is scripts makes the
following assumptions:
1. Every charm in the bundle has a `_github_repo_name` metadata field,
   containing the repository name of the charm (the org is assumed to be
   canonical)
2. Every charm in the bundle ahs a `_github_repo_branch` metadata field,
   containing the branch of the source code

```bash
./scripts/airgapped/get-all-images.sh releases/1.7/stable/kubeflow/bundle.yaml > images.txt
```

## Pull images to docker cache

We have a couple of scripts that are using `docker` commands to pull images,
retag them and compress them in a  final `tar.gz` file. To save time on those
operations it's crucial to be able to first download/cache a list of images.

```bash
python3 scripts/airgapped/save-images-to-cache.py images.txt
```

## Retag images to cache

In airgap environments users push their images in their own registries. So we'll
need to rename prefixes like `docker.io` to the server that users would use.

In our testing case our server is not DNS reachable from the machine. Instead
we directly access it with its IP and port `172.17.0.2:5000`

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

Note that in the example bellow I used the `retagged-images.txt` which was
produced from the retag-images script.

```bash
python3 scripts/airgapped/save-images-to-tar.py retagged-images.txt
```

## Save charms to tar

Users in an airgap env will need to deploy charms from local files. To assist this
we'll use this script to create a `tar.gz` containing all the charms referenced
in a bundle.

```bash
BUNDLE_PATH=releases/1.7/stable/kubeflow/bundle.yaml

python3 scripts/airgapped/save-charms-to-tar.py \
    $BUNDLE_PATH \
    --zip-all \
    --delete-afterwards
```
