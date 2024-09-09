# Utility Script

This directory contains helper scripts for Charmed Kubeflow, during CI and not only.

## Gather images used by a bundle

You can get a list of all the OCI images used by the bundle by running the following command:
```bash
pip3 install -r scripts/requirements.txt

python3 scripts/get-all-images.py \
    --append-images tests/airgapped/1.9/ckf-1.9-testing-images.txt \
    releases/1.9/stable/bundle.yaml \
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
