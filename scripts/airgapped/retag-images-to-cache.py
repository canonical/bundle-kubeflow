import argparse
import logging

import docker

from utils import (delete_file_if_exists, get_images_list_from_file,
                   get_or_pull_image)

cli = docker.client.from_env()

log = logging.getLogger(__name__)

RETAGGED_IMAGES_FILE = "retagged-images.txt"
SHA_TOKEN = "@sha256"
REGISTRIES = ["docker.io/library", "docker.io", "gcr.io", "quay.io",
              "registry.k8s.io", "k8s.gcr.io", "public.ecr.aws", "ghcr.io",
              "nvcr.io"]


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

    for registry in REGISTRIES:
        if registry not in image_nm:
            continue

        return image_nm.replace(registry, new_registry)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retag list of images")
    parser.add_argument("images")
    parser.add_argument("--new-registry", default="172.17.0.2:5000")
    # The reason we are using this IP as new registry is because this will end
    # up being the IP of the Registry we'll run as a Container. We'll need to
    # do docker push <...> so we'll have to use the IP directly, or mess with
    # the environment's /etc/hosts file

    args = parser.parse_args()

    images_ls = get_images_list_from_file(args.images)
    images_len = len(images_ls)
    new_images_ls = []
    for idx, image_nm in enumerate(images_ls):
        log.info("%s/%s", idx + 1, images_len)

        retagged_image_nm = get_retagged_image_name(
            image_nm, args.new_registry
        )

        img = get_or_pull_image(image_nm)
        logging.info("%s: Retagging to %s", image_nm, retagged_image_nm)
        img.tag(retagged_image_nm)

        new_images_ls.append(retagged_image_nm)

    log.info("Saving the produced list of images.")
    delete_file_if_exists(RETAGGED_IMAGES_FILE)
    with open(RETAGGED_IMAGES_FILE, "w+") as f:
        f.write("\n".join(new_images_ls))

    log.info("Successfully saved list of images in '%s'", RETAGGED_IMAGES_FILE)
