# This script is based on the following upstream script:
# https://github.com/kubeflow/manifests/blob/0837fb9cf3ec73f51cbddff656a160cb258eaad5/tests/trivy_scan.py

import os
import subprocess
import re
import argparse
import tempfile

# Dictionary mapping Kubeflow workgroups to directories containing kustomization files
wg_dirs = {
    "katib": "../applications/katib/upstream/installs",
    "pipelines": "../applications/pipeline/upstream/env/cert-manager/platform-agnostic-multi-user",
    "trainer": "../applications/training-operator/upstream/overlays ../applications/trainer/overlays",
    "manifests": "../common/cert-manager/cert-manager/base ../common/cert-manager/kubeflow-issuer/base ../common/istio/istio-crds/base ../common/istio/istio-namespace/base ../common/istio/istio-install/overlays/oauth2-proxy ../common/oauth2-proxy/overlays/m2m-self-signed ../common/dex/overlays/oauth2-proxy ../common/knative/knative-serving/overlays/gateways ../common/knative/knative-eventing/base ../common/istio/cluster-local-gateway/base ../common/kubeflow-namespace/base ../common/kubeflow-roles/base ../common/istio/kubeflow-istio-resources/base",
    "workbenches": "../applications/pvcviewer-controller/upstream/base ../applications/admission-webhook/upstream/overlays ../applications/centraldashboard/overlays ../applications/jupyter/jupyter-web-app/upstream/overlays ../applications/volumes-web-app/upstream/overlays ../applications/tensorboard/tensorboards-web-app/upstream/overlays ../applications/profiles/upstream/overlays ../applications/jupyter/notebook-controller/upstream/overlays ../applications/tensorboard/tensorboard-controller/upstream/overlays",
    "kserve": "../applications/kserve - ../applications/kserve/models-web-app/overlays/kubeflow",
    "model-registry": "../applications/model-registry/upstream/overlays/db ../applications/model-registry/upstream/options/istio ../applications/model-registry/upstream/options/ui/overlays/istio",
    "spark": "../applications/spark/spark-operator/overlays/kubeflow",
}

SCRIPT_DIRECTORY = os.getcwd()
IMAGES_DIRECTORY = os.path.join(SCRIPT_DIRECTORY, "images")
os.makedirs(IMAGES_DIRECTORY, exist_ok=True)

def log(*args, **kwargs):
    # Custom log function that print messages with flush=True by default.
    kwargs.setdefault("flush", True)
    print(*args, **kwargs)


def save_images(wg, images, version):
    # Saves a list of container images to a text file named after the workgroup and version.
    output_file = os.path.join(IMAGES_DIRECTORY, f"kf_{version}_{wg}_images.txt")
    with open(output_file, "w") as f:
        f.write("\n".join(images))
    log(f"File {output_file} successfully created")


def validate_semantic_version(version):
    # Validates a semantic version string (e.g., "0.1.2" or "latest").
    regex = r"^[0-9]+\.[0-9]+\.[0-9]+$"
    if re.match(regex, version) or version == "latest":
        return version
    else:
        raise ValueError(f"Invalid semantic version: '{version}'")
    

def extract_images(version, skip_list=None):
    if skip_list is None:
        skip_list = []
    version = validate_semantic_version(version)
    log(f"Running the script using Kubeflow version: {version}")

    if skip_list:
        log(f"Skipping workgroups: {', '.join(skip_list)}")

    all_images = set()  # Collect all unique images across workgroups

    for wg, dirs in wg_dirs.items():
        # Skip this workgroup if it was provided in the --skip argument
        if wg in skip_list:
            continue
        wg_images = set()  # Collect unique images for this workgroup
        for dir_path in dirs.split():
            for root, _, files in os.walk(dir_path):
                for file in files:
                    if file in [
                        "kustomization.yaml",
                        "kustomization.yml",
                        "Kustomization",
                    ]:
                        full_path = os.path.join(root, file)
                        try:
                            # Execute `kustomize build` to render the kustomization file
                            result = subprocess.run(
                                ["kustomize", "build", root],
                                check=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                            )
                        except subprocess.CalledProcessError as e:
                            log(
                                f'ERROR:\t Failed "kustomize build" command for directory: {root}. See error above'
                            )
                            continue

                        # Use regex to find lines with 'image: <image-name>:<version>' or 'image: <image-name>'
                        # and '- image: <image-name>:<version>' but avoid environment variables
                        kustomize_images = re.findall(
                            r"^\s*-?\s*image:\s*([^$\s:]+(?:\:[^\s]+)?)$",
                            result.stdout,
                            re.MULTILINE,
                        )
                        wg_images.update(kustomize_images)

        # Ensure uniqueness within workgroup images
        uniq_wg_images = sorted(wg_images)
        all_images.update(uniq_wg_images)
        save_images(wg, uniq_wg_images, version)

    # Ensure uniqueness across all workgroups
    uniq_images = sorted(all_images)
    save_images("all", uniq_images, version)

    
def clone_and_extract_images(ref, skip_list):
    """Clone kubeflow/manifests repository temporarily, and extract the images."""
    repo_url = "https://github.com/kubeflow/manifests.git"

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            clone_cmd = ["git", "clone", "--depth", "1"]
            if ref != "latest":
                clone_cmd.extend(["--branch", ref])
            # Clone into the temp directory (shallow clone for speed)
            log(f"Cloning repository: {repo_url}")
            clone_cmd.extend([repo_url, "manifests"])
            subprocess.run(
                clone_cmd,
                cwd=temp_dir, 
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError as e:
            log(f"ERROR: Failed to clone repository. Details: {e}")
            exit(1)

        repo_path = os.path.join(temp_dir, "manifests")
        tests_path = os.path.join(repo_path, "tests")
        os.chdir(tests_path)

        extract_images(version, skip_list)

        os.chdir(SCRIPT_DIRECTORY)


parser = argparse.ArgumentParser(
    description="Extract images from Kubeflow kustomizations."
)
# Define a positional argument 'version' with optional occurrence and default value 'latest'. You can run this file as python3 <filename>.py or python <filename>.py <version>
parser.add_argument(
    "version",
    type=str,
    help="Kubeflow version tag or branch to use (e.g. 'v1.11.0, 26.03-rc.1, or 'latest' which pulls from main).",
)
# Skip any specified workgroups
parser.add_argument(
    "--skip",
    nargs="*",
    type=str,
    default=["spark", "model-registry"],
    help="List of workgroups to skip (e.g., --skip katib spark manifests). Defaults to [spark, model-registry]",
)
args = parser.parse_args()
clone_and_extract_images(args.version, args.skip)
