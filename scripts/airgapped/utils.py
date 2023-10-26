import logging
import os

import docker

cli = docker.client.from_env()

LOG_FORMAT = "%(levelname)s \t| %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)

log = logging.getLogger(__name__)


def delete_file_if_exists(file_name):
    """Delete the file name if it exists."""
    if os.path.exists(file_name):
        try:
            os.remove(file_name)
            log.info("File '%s' deleted successfully.", file_name)
        except Exception as e:
            log.error("An error occurred while deleting the file:", e)


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
