# Utility Script

This directory contains helper scripts for Charmed Kubeflow, during CI and not only.

## Gather images used by a bundle

You can get a list of all the OCI images used by the bundle by running the following command:

```bash
pip3 install -r scripts/requirements.txt

python3 scripts/get_all_images.py \
    --append-images tests/airgapped/1.9/testing-images.txt \
    releases/1.9/stable/bundle.yaml \
    > images-all.txt
```

For Charmed Kubeflow 1.8, run

```bash
pip3 install -r scripts/requirements.txt

python3 scripts/get_all_images.py \
    --append-images tests/airgapped/1.8/testing-images.txt \
    releases/1.9/stable/kubeflow/bundle.yaml \
    > images-all.txt
```

The script will gather the images in the following way:

1. For each `application` in the provided `bundle.yaml` file:
2. detect if it's owned by us or another team (by looking at the `_github_dependency_repo_name` and such metadata)
3. clone its repo, by looking at `_github_repo_name` and such metadata
4. If owned by another team: only parse it's `metadata.yaml` and look for `oci-resources`
5. If owned by us: run the `tools/get-images.sh` script the repo **must** have
6. If a repo does not have `tools/get-images.sh` (i.e. kubeflow-roles) then the script should skip the repo
7. If the `get-images.sh` script either fails (return code non zero) or has error logs then the script should **fail**
8. Aggregate the outputs of all `get-images.sh` scripts to one output
9. If user passed an argument `--append-images` then the script will amend a list of images we need for airgap testing

## Produce SBOM for images in a bundle

### Prerequisites

1. Install `syft` snap

```
sudo snap install syft --classic
```

2. Install `docker` snap

```
sudo snap install docker
```

Setup `docker` snap to run as a normal user by following the snap [documentation](https://snapcraft.io/docker).

3. Create a venv and install python requirements.
   Note that python version 3.10 is required to run the script.

```
python3 -m venv venv
source venv/bin/activate

pip3 install -r scripts/requirements.txt
```

### Run SBOM producing script for images

You can get a list of all the SBOMs for the images used by the bundle by running the following command:

```
python3 scripts/get_bundle_images_sbom.py <bundle_path>
```

For example for the 1.9 bundle, run:

```
python3 scripts/get_bundle_images_sbom.py releases/1.9/stable/bundle.yaml
```

> [!WARNING]
> To produce the SBOMs of all images in the bundle (~100 images), the script can take up to a few hours depending on the network and processing resources.

The script creates a compressed file under the repo's root with the name `images_SBOM.tar.gz`. The script will store all the SBOMs there. For each image, there will be the SBOM file formatted as `<image_name>.spdx.json` inside the compressed file.

---

## Produce SBOM for charms, snaps, and bundles with sbomber

### Prerequisites

* Setup Canonical VPN.
* Install and setup `sbomber` according to [sbomber documentation](https://github.com/canonical/sbomber).
* Familiarize yourself with how `sbomber` works.

### Step 1: Identify Products for SBOM Generation

For example, in the 25.10 cycle, generate SBOMs for:

* Kubeflow bundle
* MLflow bundle
* Feast charms
* DSS snap

### Step 2: Prepare Bundle Files

1. Place the bundle file in the working folder.
2. Transform the bundle file into a `manifest.yaml` containing SBOM artifacts:

```bash
./generate_sbom_artifacts.py bundle.yaml --clients sbom --email your.email@canonical.com
```

**Notes:**

* `--clients` supports `sbom` and `secscan`. You can specify both with `--clients sbom,secscan`. Default is `sbom`.
* Provide your email.
* After this step, `manifest.yaml` will be generated.

### Step 3: Non-Bundle Components

For charms or snaps, manually create `manifest.yaml`. Example manifest files can be found in sboms_manifests_<release> directory.

### Step 4: Prepare SBOM Artifacts

```bash
./sbomber prepare manifest.yaml
```

### Step 5: Submit SBOM Requests

```bash
./sbomber submit
```

*(This may take hours for large bundles.)*

### Step 6: Poll for Completion

```bash
./sbomber poll --wait --timeout 240
```

You will get email notifications for each charm.

### Step 7: Download SBOMs

```bash
./sbomber download --reports-dir=./sbomber-reports/
```

All SBOMs will be stored in `./sbomber-reports/`.
