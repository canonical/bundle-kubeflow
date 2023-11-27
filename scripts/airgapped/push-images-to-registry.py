import argparse
import logging

import docker

from utils import get_images_list_from_file

docker_client = docker.client.from_env()

log = logging.getLogger(__name__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Push images from list.")
    parser.add_argument("images")
    args = parser.parse_args()

    images_ls = get_images_list_from_file(args.images)
    images_len = len(images_ls)
    new_images_ls = []
    for idx, image_nm in enumerate(images_ls):
        log.info("%s/%s", idx + 1, images_len)

        logging.info("Pushing image: %s", image_nm)
        docker_client.images.push(image_nm)

    log.info("Successfully pushed all images!")
