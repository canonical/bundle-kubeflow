import argparse
import logging
import os
from pathlib import Path
import subprocess
import tarfile

SBOM_DIR = "images_SBOM"

log = logging.getLogger(__name__)


def get_images_sbom(images: list[str]) -> None:

    log.info(f"Images received as input: {images}")

    sbom_path = Path(SBOM_DIR)
    sbom_path.mkdir(parents=True, exist_ok=True)

    total = len(images)

    for idx, image in enumerate(images, start=1):
        output_file = sbom_path / f"{image}.spdx.json"

        if output_file.exists():
            log.info(
                f"[{idx}/{total}] Skipping {image}, SBOM already exists at {output_file}"
            )
            continue

        log.info(f"[{idx}/{total}] Creating SBOM for {image}")
        try:
            subprocess.check_call(
                ["syft", "scan", image, "-o", f"spdx-json={image}.spdx.json"],
                cwd=SBOM_DIR,
            )
        except subprocess.CalledProcessError as e:
            log.error(f"Error scanning {image}: {e}")
            raise

    sbom_files = os.listdir(SBOM_DIR)

    # Make .tar.gz from all SBOMs
    with tarfile.open(f"{SBOM_DIR}.tar.gz", "w:gz") as tar:
        for file in sbom_files:
            tar.add(f"{SBOM_DIR}/{file}")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s - %(message)s",
    )
    parser = argparse.ArgumentParser(description="Get SBOMs for a list of images.")
    parser.add_argument(
        "images_file",
        help="Path to a file containing container images (one per line).",
    )

    args = parser.parse_args()

    images_file_path = Path(args.images_file)
    if not images_file_path.exists():
        raise FileNotFoundError(f"Images file not found: {images_file_path}")

    with images_file_path.open("r") as f:
        images_list = [line.strip() for line in f if line.strip()]

    get_images_sbom(images_list)


if __name__ == "__main__":
    main()
