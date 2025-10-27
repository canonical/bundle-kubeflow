import argparse
import csv
import json
import logging
import subprocess
import sys
import tenacity

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
MERGED_REPORT_CSV_FILE = "vulnerability_report_merged.csv"


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


def scan_images(image_file: str, kev_file_path: str, output_csv_file: str):
    CSV_HEADERS = [
        "CVE",
        "Is KEV?",
        "Severity",
        "NVD/CVSS Score",
        "Vulnerability Name",
        "Description",
        "Affected Component",
        "Notification source",
        "Relevant to Product?",
        "Affected Releases",
        "Can it be remediated?",
        "Does a patch exist?",
        "Patch Source",
        "Details",
        "Remediation status",
        "Patched Release",
        "Timestamp",
        "Jira Ticket",
        "Notes",
    ]

    with open(image_file, "r") as file:
        lines = [line.strip() for line in file]

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

    with open(output_csv_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
        writer.writeheader()

        seen_vulnerabilities = set()

        for image_name in lines:
            vulnerability_count = 0

            data = run_trivy_scan(image_name)
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

                    row_dict = {
                        "CVE": vulnerability.get("VulnerabilityID", "N/A"),
                        "Is KEV?": is_kev,
                        "Severity": vulnerability.get("Severity", "N/A").capitalize(),
                        "NVD/CVSS Score": vulnerability.get("CVSS", {})
                        .get("nvd", {})
                        .get("V3Score", "N/A"),
                        "Vulnerability Name": vulnerability.get("Title", "N/A"),
                        "Description": vulnerability.get("Description", "N/A"),
                        "Affected Component": image_name,
                        "Notification source": "trivy version 0.66.0",
                        "Relevant to Product?": "Yes",
                        "Affected Releases": "Kubeflow 1.10",
                        "Can it be remediated?": can_be_remediated,
                        "Does a patch exist?": can_be_remediated,
                        "Patch Source": patch_source,
                        "Remediation status": "Pending",
                        "Patched Release": fixed_version,
                    }
                    writer.writerow(row_dict)
            logger.info(f"Found {vulnerability_count} vulnerabilities")


# We also want to merge CVEs, so only one entry exists for each CVE
def merge_cve(input_csv_file: str, output_csv_file: str, add_headers=False):
    """Merge CVEs with same ID on different images"""
    merged_data = {}
    with open(input_csv_file, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames
        for row in reader:
            cve_id = row.get("CVE")

            # Create a unique key for each vulnerability
            unique_key = cve_id

            # Get the current list of components from the row, splitting by comma and space
            current_components = {
                comp.strip()
                for comp in row.get("Affected Component", "").split(",")
                if comp.strip()
            }

            if unique_key in merged_data:
                merged_data[unique_key]["Affected Component"].update(current_components)
            else:
                row["Affected Component"] = current_components
                merged_data[unique_key] = row

    with open(output_csv_file, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=headers)
        if add_headers:
            writer.writeheader()

        for data_row in merged_data.values():
            # Join the set of components back into a single, sorted, comma-separated string
            data_row["Affected Component"] = ", ".join(
                sorted(list(data_row["Affected Component"]))
            )
            if data_row.get("Severity"):
                data_row["Severity"] = data_row["Severity"].capitalize()
            writer.writerow(data_row)
        logger.info(f"All vulnerabilities have been written to {output_csv_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "IMAGES_FILE",
        type=str,
        help="The path to the input text file containing image paths.",
    )
    args = parser.parse_args()
    scan_images(args.IMAGES_FILE, KEV_FILE, REPORT_CSV_FILE)
    merge_cve(REPORT_CSV_FILE, MERGED_REPORT_CSV_FILE, add_headers=True)
