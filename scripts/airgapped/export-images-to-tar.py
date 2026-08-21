import argparse
import logging
import os
import subprocess

import docker

from utils import (save_image, get_images_list_from_file,
                   get_or_pull_image, get_retagged_image_name, delete_file_if_exists)

cli = docker.client.from_env()

log = logging.getLogger(__name__)




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create tar.gz from images")
    parser.add_argument("images")
    parser.add_argument("--prefix", default="")
    parser.add_argument("--new-registry", default="")

    args = parser.parse_args()

    images_ls = get_images_list_from_file(args.images)
    images_len = len(images_ls)
    tar_files = []
    for idx, image_nm in enumerate(images_ls):
        log.info("%s/%s", idx + 1, images_len)

        log.info("%s: Pulling image", image_nm)

        img = get_or_pull_image(image_nm)

        if args.new_registry:
            retagged_image_nm = get_retagged_image_name(
                image_nm, args.new_registry
            )

            log.info("%s: Retagging to %s", image_nm, retagged_image_nm)
            img.tag(retagged_image_nm)
        else:
            retagged_image_nm = None

        tar_file = save_image(args.prefix, retagged_image_nm or image_nm)
        tar_files.append(tar_file)

    log.info("Creating final tar.gz file. Will take a while...")
    subprocess.run(["tar", "-cv", "--use-compress-program=pigz", "-C", args.prefix,
                    "-f", f"{args.prefix}/images.tar.gz", *[f.removeprefix(args.prefix) for f in tar_files]])
    log.info("Created the tar.gz file!")

    log.info("Deleting intermediate .tar files.")
    for file in tar_files:
        delete_file_if_exists(file)
    log.info("Deleted all .tar files.")
        
