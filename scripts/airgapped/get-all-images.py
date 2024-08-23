import argparse
import logging
import shutil
import subprocess

import git
import yaml

# logging
LOG_FORMAT = "%(levelname)s \t| %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
log = logging.getLogger(__name__)

# consts
EXCLUDE_REPOS = ["kubeflow-roles"]

GH_REPO_KEY = "_github_repo_name"
GH_BRANCH_KEY = "_github_repo_branch"
GH_DEPENDENCY_REPO_KEY = "_github_dependency_repo_name"
GH_DEPENDENCY_BRANCH_KEY = "_github_dependency_repo_branch"
GET_IMAGES_SH = "tools/get-images.sh"

AIRGAP_TESTING_IMAGES = [
    "charmedkubeflow/pipelines-runner:ckf-1.8",
    "docker.io/kubeflowkatib/simple-pbt:v0.16.0",
    "ghcr.io/knative/helloworld-go:latest",
    "gcr.io/kubeflow-ci/tf-mnist-with-summaries:1.0",
]


def is_dependency_app(app: dict) -> bool:
    """Detect if app in bundle is not owned by Analytics team."""
    if GH_DEPENDENCY_REPO_KEY in app and GH_DEPENDENCY_BRANCH_KEY in app:
        return True

    return False


def bundle_app_contains_gh_metadata(app: dict) -> bool:
    """
    Given an application in a bundle check if it contains github metadata keys
    to be able to be parsed properly.
    """
    if is_dependency_app(app):
        return True

    if GH_REPO_KEY in app and GH_BRANCH_KEY in app:
        return True

    return False


def clone_repo(repo_name: str, branch: str) -> str:
    """Clones locally a repo and returns the folder created."""
    repo_url = f"https://github.com/canonical/{repo_name}.git"

    logging.info(f"Cloning repo {repo_url}")
    repo = git.Repo.clone_from(repo_url, str(repo_name))

    logging.info(f"Checking out to branch {branch}")
    repo.git.checkout(branch)

    return repo_name


def get_analytics_app_images(app: dict) -> list[str]:
    """
    This function gets the images used by a charm developed by us, by:
    1. Cloning the repo of the charm
    2. Running the repo's tools/get-images.sh
    3. Delete the repo

    If the tools/get-images.sh of a repo fails for any reason then this
    script will also fail.
    """
    images = []
    repo_dir = clone_repo(app[GH_REPO_KEY], app[GH_BRANCH_KEY])

    logging.info(f"Executing repo's {GET_IMAGES_SH} script")
    process = subprocess.Popen(["bash", "tools/get-images.sh"], cwd=repo_dir,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if stderr:
        raise ValueError("Script '%s' for charm '%s' had error logs: \n%s" %
                         (GET_IMAGES_SH, app["charm"], stderr.decode("utf-8"))
                         )
    images = stdout.decode("utf-8").split("\n")

    # cleanup
    shutil.rmtree(repo_dir)
    return images


def get_dependency_app_images(app: dict) -> list[str]:
    """
    This function gets the images used by a dependency charm by:
    1. Cloning the repo of the charm
    2. Looking at its metadata.yaml for "upstream-source" keys
    3. Delete the repo
    """
    images = []
    repo_dir = clone_repo(app[GH_DEPENDENCY_REPO_KEY],
                          app[GH_DEPENDENCY_BRANCH_KEY])
    with open("%s/metadata.yaml" % repo_dir, 'r') as metadata_file:
        metadata_dict = yaml.safe_load(metadata_file)

    for _, rsrc in metadata_dict["resources"].items():
        if "type" in rsrc and rsrc["type"] == "oci-image":
            img = rsrc["upstream-source"]
            logging.info("Found image %s" % img)
            images.append(img)

    # cleanup
    shutil.rmtree(repo_dir)
    return images


def get_bundle_images(bundle_dict: dict) -> list[str]:
    """Return a list of images used by a bundle"""
    images = []

    for app_name, app in bundle_dict["applications"].items():
        logging.info(f"Handling app {app_name}")

        # exclude repos we know don't have images
        if app_name in EXCLUDE_REPOS:
            logging.info("Ignoring charm %s", app["charm"])
            continue

        # Follow default image-gather process for dependency apps
        if is_dependency_app(app):
            logging.info("Dependency app '%s' with charm '%s'", app_name,
                         app["charm"])
            images.extend(get_dependency_app_images(app))
            continue

        # Ensure analytics app has necessary github repo/branch metadata
        if not bundle_app_contains_gh_metadata(app):
            raise KeyError(
                "Application '%s' doesn't include expected gh metadata keys" %
                app_name
            )

        images.extend(get_analytics_app_images(app))

    return images


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Gather all images from a bundle"
    )
    parser.add_argument("bundle")
    parser.add_argument("--airgap-testing", action="store_true")

    args = parser.parse_args()

    bundle_dict = {}
    with open(args.bundle, 'r') as file:
        bundle_dict = yaml.safe_load(file)

    # keep unique images and sort them
    images_set = set(get_bundle_images(bundle_dict))
    if '' in images_set:
        images_set.remove('')

    images = list(images_set)
    images.sort()

    # append the airgap images
    if args.airgap_testing:
        images.extend(AIRGAP_TESTING_IMAGES)

    logging.info(f"Found {len(images)} different images")

    for img in images:
        print(img)
