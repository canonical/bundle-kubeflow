import argparse
import logging

import docker

from utils import get_images_list_from_file, get_or_pull_image

cli = docker.client.from_env()

log = logging.getLogger(__name__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pull locally list of images")
    parser.add_argument("images")
    args = parser.parse_args()

    images_ls = get_images_list_from_file(args.images)
    images_len = len(images_ls)
    for idx, image in enumerate(images_ls):
        log.info("%s/%s", idx + 1, images_len)
        get_or_pull_image(image)
