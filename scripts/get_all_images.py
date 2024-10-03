#!/usr/bin/env python3

import argparse
import logging
import subprocess
import os
import sys
import contextlib
import tempfile

import git
import yaml

from typing import Iterator
from pathlib import Path

# logging
LOG_FORMAT = "%(levelname)s \t| %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
log = logging.getLogger(__name__)

# consts
EXCLUDE_CHARMS = ["kubeflow-roles"]

GH_REPO_KEY = "_github_repo_name"
GH_BRANCH_KEY = "_github_repo_branch"
GH_DEPENDENCY_REPO_KEY = "_github_dependency_repo_name"
GH_DEPENDENCY_BRANCH_KEY = "_github_dependency_repo_branch"
GET_IMAGES_SH = "tools/get-images.sh"


def is_dependency_app(app: dict) -> bool:
    """
    Return True if app in bundle is not owned by Analytics team, False
    otherwise.

    Args:
        app(dict): app metadata from a bundle.yaml in dictionary form

    Returns:
        True if app has GH dependency metadata, else False
    """
    if GH_DEPENDENCY_REPO_KEY in app and GH_DEPENDENCY_BRANCH_KEY in app:
        return True

    return False


def bundle_app_contains_gh_metadata(app: dict) -> bool:
    """
    Given an application in a bundle check if it contains github metadata keys
    to be able to be parsed properly.

    Args:
        app(dict): app metadata from a bundle.yaml in dictionary form

    Returns:
        True if app has GH metadata, else False
    """
    if is_dependency_app(app):
        return True

    if GH_REPO_KEY in app and GH_BRANCH_KEY in app:
        return True

    return False


def validate_bundle(bundle: dict):
    """
    Given a bundle, parse all the applications and ensure they contain the
    correct metadata.

    Args:
        bundle: Dictionary of the loaded bundle
    """
    for app_name, app in bundle["applications"].items():
        if bundle_app_contains_gh_metadata(app):
            continue

        logging.error("Application '%s' doesn't include expected gh metadata keys.",
                      app_name)
        sys.exit(1)


@contextlib.contextmanager
def clone_git_repo(repo_name: str, branch: str) -> Iterator[git.PathLike]:
    """
    Clones locally a repo and returns the path of the folder created.

    Args:
        repo_name(str): name of the repo to clone
        branch(str): branch to checkout to, once cloned the repo
    """
    repo_url = f"https://github.com/canonical/{repo_name}.git"

    # we can't use the default /tmp/ dir because of
    # https://github.com/mikefarah/yq/issues/1808
    with tempfile.TemporaryDirectory(dir=os.getcwd()) as tmp:
        logging.info(f"Cloning repo {repo_url}")
        repo = git.Repo.clone_from(repo_url, tmp)

        logging.info(f"Checking out to branch {branch}")
        repo.git.checkout(branch)

        yield repo.working_dir


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
    repo_name = app[GH_REPO_KEY]
    repo_branch = app[GH_BRANCH_KEY]

    with clone_git_repo(repo_name, repo_branch) as repo_dir:
        logging.info(f"Executing repo's {GET_IMAGES_SH} script")
        try:
            process = subprocess.run(["bash", "tools/get-images.sh"],
                                     cwd=repo_dir, capture_output=True,
                                     text=True, check=True)
        except subprocess.CalledProcessError as exc:
            logging.error("Script '%s' for charm '%s' failed: %s",
                          GET_IMAGES_SH, app["charm"], exc.stderr)
            raise exc

    images = process.stdout.strip().split("\n")

    logging.info("Found the following images:")
    for image in images:
        logging.info("* " + image)

    return images


def get_dependency_app_images(app: dict) -> list[str]:
    """
    This function gets the images used by a dependency charm by:
    1. Cloning the repo of the charm
    2. Looking at its metadata.yaml for "upstream-source" keys
    3. Delete the repo
    """
    images = []
    repo_name = app[GH_DEPENDENCY_REPO_KEY]
    repo_branch = app[GH_DEPENDENCY_BRANCH_KEY]
    with clone_git_repo(repo_name, repo_branch) as repo_dir:
        metatada_file = f"{repo_dir}/metadata.yaml"
        metadata_dict = yaml.safe_load(Path(metatada_file).read_text())

        for _, rsrc in metadata_dict["resources"].items():
            if rsrc.get("type", "") != "oci-image":
                continue

            images.append(rsrc["upstream-source"])

    logging.info("Found the following images:")
    for image in images:
        logging.info("* " + image)

    return images


def cleanup_images(images: list[str]) -> list[str]:
    """
    Given a list of OCI registry images ensure
    1. there are no duplicates
    2. there are no images with empty name
    3. the list is sorted

    Args:
        images: List of images to be processed

    Returns:
        A list with unique and sorted values.
    """
    images_set = set(images)
    if "" in images_set:
        images_set.remove('')

    unique_images = list(images_set)
    unique_images.sort()

    return unique_images


def get_bundle_images(bundle_path: str) -> list[str]:
    """Return a list of images used by a bundle"""
    bundle_dict = yaml.safe_load(Path(bundle_path).read_text())
    validate_bundle(bundle_dict)

    images = []

    for app_name, app in bundle_dict["applications"].items():
        logging.info(f"Handling app {app_name}")

        # exclude repos we know don't have images
        # if we find we keep extending this const, we should introduce an
        # argument in the script for dynamically exluding repos/charms
        if app_name in EXCLUDE_CHARMS:
            logging.info("Ignoring charm %s", app["charm"])
            continue

        # Follow default image-gather process for dependency apps
        if is_dependency_app(app):
            logging.info("Dependency app '%s' with charm '%s'", app_name,
                         app["charm"])
            images.extend(get_dependency_app_images(app))
            continue

        # image from analytics team
        images.extend(get_analytics_app_images(app))

    return cleanup_images(images)


def get_static_images_from_file(images_file_path: str) -> list[str]:
    """
    Return a list of images stored in a text file and separated by \n.

    Args:
        images_file_path: Path of the file containing images

    Returns:
        list of strings, containing the images in the file
    """
    with open(images_file_path, "r") as file:
        images = file.readlines()

    cleaned_images = [image.strip() for image in images]
    for image in cleaned_images:
        logging.info(image)

    return cleaned_images


def main():
    parser = argparse.ArgumentParser(
        description="Gather all images from a bundle"
    )
    parser.add_argument("bundle")
    parser.add_argument("--append-images",
                        help="Appends list of images from input file.")

    args = parser.parse_args()

    images = get_bundle_images(args.bundle)

    # append the airgap images
    if args.append_images:
        logging.info("Appending images found in file '%s'", args.append_images)
        extra_images = get_static_images_from_file(args.append_images)
        images.extend(extra_images)

    logging.info(f"Found {len(images)} different images")

    for img in images:
        print(img)


if __name__ == "__main__":
    main()
