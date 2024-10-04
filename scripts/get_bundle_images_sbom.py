import argparse
import logging
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

from get_all_images import get_bundle_images

SBOM_DIR = "images_SBOM"

log = logging.getLogger(__name__)


def get_bundle_images_sbom(bundle_path: str) -> None:

    # get a list of images in the bundle
    bundle_images = get_bundle_images(bundle_path)

    log.info(f"Images gathered from the bundle: {bundle_images}")

    Path(SBOM_DIR).mkdir(parents=True, exist_ok=True)

    for image in bundle_images:
        log.info(f"Creating SBOM for {image}")
        try:
            subprocess.check_call(
                ['syft', 'scan', image, '-o', f'spdx-json={image}.spdx.json'],
                cwd=SBOM_DIR,
            )
        except subprocess.CalledProcessError as e:
            log.error(f"Error scanning {image}: {e.output}")
            raise e

    sbom_files = os.listdir(SBOM_DIR)

    # Make .tar.gz from all SBOMs
    with tarfile.open(f"{SBOM_DIR}.tar.gz", "w:gz") as tar:
        for file in sbom_files:
            tar.add(f"{SBOM_DIR}/{file}")

    # Cleanup files
    shutil.rmtree(SBOM_DIR)


def main():
    parser = argparse.ArgumentParser(description="Get SBOMs for all images in a bundle.")
    parser.add_argument("bundle", help="the bundle.yaml file to be scanned.")

    args = parser.parse_args()

    get_bundle_images_sbom(args.bundle)


if __name__ == "__main__":
    main()
