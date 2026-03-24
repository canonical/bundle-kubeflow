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


def ensure_file_path(file: str):
    """Ensure a given file path actually exists."""
    image_file = Path(file)
    if not image_file.is_file():
        raise argparse.ArgumentTypeError(f"Input file does not exist: {image_file}")
    return image_file


def ensure_dir_path(directory: str):
    """Ensure a given directory path exists, create it if it doesn't."""
    output_dir = Path(directory)
    if output_dir.exists():
        logging.info(f"Directory already exists: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


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
        logging.error(f"Trivy scan failed for {image} (exit code {result.returncode})")
        if result.stderr:
            logging.error(f"stderr:\n{result.stderr.strip()}")
        raise RuntimeError(f"Trivy failed for {image}")
    logging.info(f"Scan completed for {image} in {duration:.2f}")
    if result.stderr:
        logging.debug(f"Trivy stderr:\n{result.stderr.strip()}")


def main():
    """Receive image list as an argument, and output"""
    parser = argparse.ArgumentParser(
        description="Scan container images with Trivy and generate reports."
    )
    parser.add_argument("file", help="File containing list of images", type=ensure_file_path)
    parser.add_argument(
        "-o",
        "--output",
        default="trivy-reports",
        help="Directory where trivy reports will be stored (default: trivy-reports)",
        type=ensure_dir_path
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()
    configure_logging(args.verbose)
    
    logging.info(f"Scanning container images specified in {args.file}")
    images = [
        line.strip() for line in args.file.read_text().splitlines() if line.strip()
    ]

    for image in images:
        normalized = normalize_image_name(image)
        report_path = args.output / f"{normalized}.{TRIVY_REPORT_TYPE}"
        logging.info(f"Scanning image {image} → {report_path}")
        try:
            run_trivy(image, report_path)
        except Exception as e:
            logging.error(f"Execution failed: {e}")
            return 1
    logging.info("All scans completed.")


if __name__ == "__main__":
    sys.exit(main())
