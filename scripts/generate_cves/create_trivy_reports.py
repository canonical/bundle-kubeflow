#!/usr/bin/env python3
import argparse
import logging
import subprocess
import sys
import time
from pathlib import Path


TRIVY_REPORT_TYPE = "json"
TRIVY_TIMEOUT = "10m"
TRIVY_SKIP_FILES = "/bin/pebble,/usr/bin/pebble,usr/bin/pebble,bin/pebble"


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="| %(levelname)-7s | %(message)s",
    )


def normalize_image_name(image: str) -> str:
    """Normalize the image of the image to avoid difficult characters."""
    return image.replace(":", "-").replace("/", "-").replace(".", "-")


def run_trivy(image: str, report_path: Path) -> None:
    """Run trivy scan for an image file, and output to report_path."""
    cmd = [
        "trivy",
        "image",
        image,
        "-q",
        "--format",
        TRIVY_REPORT_TYPE,
        "-o",
        str(report_path),
        "--timeout",
        TRIVY_TIMEOUT,
        "--skip-files",
        TRIVY_SKIP_FILES,
    ]
    logging.debug(f"Executing command: {' '.join(cmd)}")
    start = time.time()
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    duration = time.time() - start
    if result.returncode != 0:
        logging.error(
            f"Trivy scan failed for {image} (exit code {result.returncode})"
        )
        if result.stderr:
            logging.error(f"stderr:\n{result.stderr.strip()}")
        raise RuntimeError(f"Trivy failed for {image}")
    logging.info(f"Scan completed for {image} in {duration:.2f}")
    if result.stderr:
        logging.debug(f"Trivy stderr:\n{result.stderr.strip()}")


def main() -> int:
    """Receive image list as an argument, and output """
    parser = argparse.ArgumentParser(
        description="Scan container images with Trivy and generate reports."
    )
    parser.add_argument("file", help="File containing list of images")
    parser.add_argument(
        "-o",
        "--output",
        default="trivy-reports",
        help="Directory where trivy reports will be stored (default: trivy-reports)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()
    configure_logging(args.verbose)
    
    image_file = Path(args.file)
    output_dir = Path(args.output)
    
    if not image_file.is_file():
        logging.error("Input file does not exist: %s", image_file)
        return 1
    if output_dir.exists():
        logging.warning(
            "%s directory already exists.",
            output_dir,
        )
    logging.info(f"Scanning container images specified in {image_file}")
    output_dir.mkdir(parents=True, exist_ok=True)
    images = [
        line.strip() for line in image_file.read_text().splitlines() if line.strip()
    ]
    
    for image in images:
        normalized = normalize_image_name(image)
        report_path = output_dir / f"{normalized}.{TRIVY_REPORT_TYPE}"
        if report_path.exists():
            logging.info(
                "Trivy report '%s' for %s already exists, skipping",
                report_path,
                image,
            )
            continue
        logging.info("Scanning image %s → %s", image, report_path)
        try:
            run_trivy(image, report_path)
        except Exception:
            return 1
    logging.info("All scans completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
