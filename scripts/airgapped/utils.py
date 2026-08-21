import logging
import os
import pathlib

import docker
import subprocess

SHA_TOKEN = "@sha256"

cli = docker.client.from_env()

LOG_FORMAT = "%(levelname)s \t| %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)

log = logging.getLogger(__name__)


def delete_files_with_extension(dir_path, extension):
    """Delete all files in dir_path that have a specific file extension."""
    dir_files = os.listdir(dir_path)
    for file in dir_files:
        if file.endswith(extension):
            os.remove(os.path.join(dir_path, file))


def delete_file_if_exists(file_name):
    """Delete the file name if it exists."""
    pathlib.Path(file_name).unlink(missing_ok=True)

def delete_image_if_exists(image):
    """Delete the image if it exists."""
    img = cli.images.get(image)

    cli.images.remove(img.id)


def get_images_list_from_file(file_name: str) -> list[str]:
    """Given a file name with \n separated names return the list of names."""
    try:
        with open(file_name, 'r') as file:
            images = file.read().splitlines()
            return images
    except FileNotFoundError:
        log.warn(f"File '{file_name}' not found.")
        return []
    except Exception as e:
        log.error("An error occurred:", e)
        return []


def get_or_pull_image(image: str):
    """First try to get the image from local cache, and then pull."""
    try:
        log.info("%s: Trying to get image from cache", image)
        img = cli.images.get(image)

        log.info("%s: Found image in cache", image)
        return img
    except docker.errors.ImageNotFound:
        log.info("%s: Couldn't find image in cache. Pulling it", image)
        img = cli.images.pull(image)

        log.info("%s: Pulled image", image)
        return img

def save_image(base_path, image_nm) -> str:
    """Given an Image object, save it as tar."""
    get_or_pull_image(image_nm)
    file_name = "%s.tar" % image_nm
    file_name = os.path.join(
        base_path,
        file_name.replace("/", "-").replace(":", "-")
    )
    if os.path.isfile(file_name):
        log.info("Tar '%s' already exists. Skipping...", file_name)
        return file_name

    log.info("%s: Saving image to tar '%s'.", image_nm, file_name)
    for i in range(10):
        # We've seen that sometimes we get socket timeouts. Try 10 times
        try:
            with open(file_name, "w+b") as f:
                subprocess.run(["docker", "save", image_nm], stdout=f)

            logging.info("%s: Saved image to tar '%s'", image_nm, file_name)
            return file_name
        except Exception as e:
            log.error("Failed to create tar file. Deleting tar '%s", file_name)
            log.error(e)
            log.info("Retrying %s/10 to store image to tar '%s'",
                     i + 1, file_name)

    log.error("Tried 10 times to create tar '%s' and failed: %s", file_name)
    delete_file_if_exists(file_name)


def retag_image_with_sha(image):
    """Retag the image by using the sha value."""
    log.info("Retagging image digest: %s", image)
    repo_digest = image.attrs["RepoDigests"][0]
    [repository_name, sha_value] = repo_digest.split("@sha256:")

    tagged_image = "%s:%s" % (repository_name, sha_value)
    log.info("Retagging to: %s", tagged_image)
    image.tag(tagged_image)

    log.info("Tagged image successfully: %s", tagged_image)
    return cli.images.get(tagged_image)


def get_retagged_image_name(image_nm: str, new_registry: str) -> str:
    """Given an image name replace the repo and use sha as tag."""
    if SHA_TOKEN in image_nm:
        log.info("Provided image has sha. Using it's value as tag.")
        image_nm = image_nm.replace(SHA_TOKEN, "")

    if len(image_nm.split("/")) == 1:
        # docker.io/library image, i.e. ubuntu:22.04
        return "%s/%s" % (new_registry, image_nm)

    if len(image_nm.split("/")) == 2:
        # classic docker.io image, i.e. argoproj/workflow-controller
        return "%s/%s" % (new_registry, image_nm)

    # There are more than 2 / in the image name. Replace first part
    # Example image: quay.io/metallb/speaker:v0.13.3
    _, image_nm = image_nm.split("/", 1)
    return "%s/%s" % (new_registry, image_nm)
