import argparse
import logging
import os
import subprocess

import docker

from utils import (delete_file_if_exists, get_images_list_from_file,
                   get_or_pull_image)

cli = docker.client.from_env()

log = logging.getLogger(__name__)


def save_image(image_nm) -> str:
    """Given an Image object, save it as tar."""
    get_or_pull_image(image_nm)
    file_name = "%s.tar" % image_nm
    file_name = file_name.replace("/", "-").replace(":", "-")
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create tar.gz from images")
    parser.add_argument("images")
    args = parser.parse_args()

    images_ls = get_images_list_from_file(args.images)
    images_len = len(images_ls)
    tar_files = []
    for idx, image_nm in enumerate(images_ls):
        log.info("%s/%s", idx + 1, images_len)
        tar_file = save_image(image_nm)
        tar_files.append(tar_file)

    log.info("Creating final tar.gz file. Will take a while...")
    subprocess.run(["tar", "-cv", "--use-compress-program=pigz",
                    "-f", "images.tar.gz", *tar_files])
    log.info("Created the tar.gz file!")

    log.info("Deleting intermediate .tar files.")
    for file in tar_files:
        delete_file_if_exists(file)
    log.info("Deleted all .tar files.")
