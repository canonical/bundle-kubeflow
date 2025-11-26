import argparse
import csv
import json
import logging
import subprocess
import sys
import typing

import tenacity

import pandas as pd
import pathlib
from pathlib import Path
from enum import Enum

# This script reads:
# - IMAGES_FILE with the images we want to scan
# - KEV_FILE with the KEVs
# and outputs:
# - REPORT_CSV_FILE
# - MERGED_REPORT_CSV_FILE with the CVEs merged by ID

LOG_FORMAT = "%(levelname)s:%(name)s: %(message)s"
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

KEV_FILE = "known_exploited_vulnerabilities.csv"
REPORT_CSV_FILE = "vulnerability_report.csv"

class ImageInputType(str, Enum):
    IMAGE_LIST_FILE = "image_list_file"
    FOLDER_REPORTS = "folder_reports"

@tenacity.retry(
    stop=tenacity.stop_after_attempt(3), wait=tenacity.wait_fixed(3), reraise=True
)
def run_trivy_scan(image_name: str) -> dict:
    logger.info(f"Scanning: {image_name}")
    process = subprocess.run(
        [
            "trivy",
            "image",
            image_name,
            "-q",
            "--format",
            "json",
            "--timeout",
            "10m",
            "--skip-files",
            "'/bin/pebble,/usr/bin/pebble,usr/bin/pebble,bin/pebble'",
        ],
        capture_output=True,
        text=True,
    )
    if process.returncode != 0:
        logger.error(f"Failed to scan {image_name}. Error: {process.stderr}")
        raise Exception(f"Trivy scan failed: {process.stderr}")
    else:
        try:
            return json.loads(process.stdout)
        except json.JSONDecodeError as e:
            logger.error("Failed to decode JSON output for {image_name}.")
            raise e


def iter_images(image_path: str):
    with open(image_path, "r") as file:
        lines = [line.strip() for line in file]

        for image_name in lines:

            json_data = run_trivy_scan(image_name)

            yield image_name, json_data


def get_output(filename: Path) -> dict:
    with open(filename, "r") as fid:
        return json.load(fid)

def get_json_files(root_path: str) -> typing.Iterator[tuple[Path, Path]]:
    for (root, dirs, files) in pathlib.os.walk(root_path):
        for _file in files:
            p = Path(_file)
            if p.suffix == ".json":
                yield Path(root).relative_to(root_path), p

def iter_reports(image_path: str):
    for folder, filename in get_json_files(image_path):
        output = get_output(Path(image_path) / folder / filename)
        yield output["ArtifactName"], output


def get_kves(kev_file_path: Path) -> set[str]:
    # Create lookup set to make it more efficient to lookup if a CVE is a KEV
    kev_cve_set = set()

    try:
        with open(kev_file_path, "r", encoding="utf-8") as kev_file:
            reader = csv.reader(kev_file)
            for row in reader:
                if row:
                    kev_cve_set.add(row[0])
        logger.info("Creating set of KEVs")
    except FileNotFoundError:
        logger.error("Could not open file")

    return kev_cve_set

def scan_images(
        iter_scans: typing.Iterator[tuple[str, dict]],
        kev_cve_set: set[str]
) -> pd.DataFrame:

    vulnerability_count = 0
    seen_vulnerabilities = set()

    rows = []

    for image_name, data in iter_scans:
        for result in data.get("Results", []):
            for vulnerability in result.get("Vulnerabilities", []):
                vuln_id = vulnerability.get("VulnerabilityID", "N/A")
                unique_vulnerability_key = (vuln_id, image_name)
                if unique_vulnerability_key in seen_vulnerabilities:
                    continue
                seen_vulnerabilities.add(unique_vulnerability_key)
                vulnerability_count += 1
                
                is_kev = (
                    "Yes"
                    if vulnerability.get("VulnerabilityID", "N/A") in kev_cve_set
                    else "No"
                )
                patch_exists = (
                    "FixedVersion" in vulnerability
                    and vulnerability["FixedVersion"]
                )
                fixed_version = (
                    vulnerability["FixedVersion"]
                    if "FixedVersion" in vulnerability
                    else "N/A"
                )
                can_be_remediated = "Yes" if patch_exists else "No"
                patch_source = (
                    vulnerability.get("References") if patch_exists else "N/A"
                )

                rows.append({
                    "CVE": vulnerability.get("VulnerabilityID", "N/A"),
                    "Package Name": vulnerability.get("PkgName", "N/A"),
                    "Version": vulnerability.get("InstalledVersion", "N/A"),
                    "Is KEV?": is_kev,
                    "Severity": vulnerability.get("Severity", "N/A").capitalize(),
                    "NVD/CVSS Score": vulnerability.get("CVSS", {})
                    .get("nvd", {})
                    .get("V3Score", "N/A"),
                    "Vulnerability Name": vulnerability.get("Title", "N/A"),
                    "Description": vulnerability.get("Description", "N/A").replace("\r", "\n"),
                    "Affected Component": image_name,
                    "Notification source": "trivy version 0.66.0",
                    "Relevant to Product?": "Yes",
                    "Affected Releases": "Kubeflow 1.10",
                    "Can it be remediated?": can_be_remediated,
                    "Does a patch exist?": can_be_remediated,
                    "Patch Source": patch_source,
                    "Remediation status": "Pending",
                    "Patched Release": fixed_version,
                })

    logger.info(f"Found {vulnerability_count} vulnerabilities")

    return pd.DataFrame.from_records(rows)

# We also want to merge CVEs, so only one entry exists for each CVE
def merge_cve(input_df: pd.DataFrame):
    """Merge CVEs with same ID on different images"""

    def reduce(subset: pd.DataFrame):
        components = ",".join(subset["Affected Component"].values)
        row = subset.iloc[0].copy(deep=True)
        row["Affected Component"] = components
        return row

    return input_df.groupby("CVE").apply(reduce, include_groups=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "IMAGES_FILE",
        type=str,
        help="The path to the input text file containing image paths.",
    )
    parser.add_argument(
        "--type",
        dest="FILE_TYPE",
        type=ImageInputType,
        default="image_list_file",
        choices=["image_list_file", "folder_reports"],
        help="The path to the input text file containing image paths.",
    )
    parser.add_argument(
        "--severity",
        dest="SEVERITY",
        action="append",
        type=str,
        help="Severity to be included in the report. Multiple severities can be provided either by as comma separated or as multiple arguments. If not provided, all of the are assumed.",
    )

    args = parser.parse_args()

    severities = {
        severity.capitalize()
        for severity in sum([severity.split(",") for severity in args.SEVERITY or []], [])
    }

    for severity in severities:
        if severity not in ["High","Low", "Medium","Critical"]:
            raise ValueError(f"severity level {severity} is not recognized") 

    logger.info(f"Selecting severities: {','.join(severities)}")
        
    data = iter_images(args.IMAGES_FILE) \
        if args.FILE_TYPE == ImageInputType.IMAGE_LIST_FILE \
        else iter_reports(args.IMAGES_FILE)

    cve_list = scan_images(data, get_kves(Path(KEV_FILE)))

    if severities:
        cve_list = cve_list[cve_list["Severity"].isin(list(severities))]
    
    merged_list = merge_cve(cve_list)

    merged_list.to_csv(REPORT_CSV_FILE)
