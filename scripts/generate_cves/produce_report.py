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
EXCEPTION_FILE="CVE_Exceptions.xlsx"
REPORT_CSV_FILE = "Vulnerability_Tracker-Charmed_Kubeflow.xlsx"

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

def get_exceptions(exception_file: Path) -> dict[str, dict[str, str]]:
    # Get the dictionary of exceptions that is structured with the following
    # structure:
    # { <CVE>: { <IMAGE>: <RATIONALE> } }

    if not exception_file.exists():
        return {}

    # The files has the following columns: Package, Version, CVE, CVSS Score, Image Name, Patchable, ETA, Rationale
    # However the first four columns represents a MultiIndex, and need to be provided as index_col below to ensure
    # the correct parsing
    df = pd.read_excel(
        exception_file, index_col=[0, 1, 2, 3]
    ).reset_index()

    selection = df[df["Patchable"]=="No"][
        ["CVE", "Image Name", "Rationale"]
    ].drop_duplicates()

    selection["Image Name"] = selection["Image Name"].apply(lambda x: x.removeprefix("docker-quarantine-local/"))

    return {
        name: group[
            ["Image Name", "Rationale"]
        ].set_index("Image Name")["Rationale"].to_dict()
        for name, group in selection.groupby("CVE")}

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

def get_upstream_cves(
        iter_scans: typing.Iterator[tuple[str, dict]]
) -> dict[str, list[str]]:

    vulns = {}

    for image_name, data in iter_scans:
        for result in data.get("Results", []):
            for vulnerability in result.get("Vulnerabilities", []):
                vuln_id = vulnerability.get("VulnerabilityID", "N/A")
                if vuln_id in vulns:
                    vulns[vuln_id].append(image_name)
                else:
                    vulns[vuln_id] = [image_name]
    return vulns

def scan_images(
        iter_scans: typing.Iterator[tuple[str, dict]],
        kev_cve_set: set[str], exceptions: dict[str, dict[str, str]],
        upstream_vulns: dict[str, list[str]] | None, actions: dict[str, dict[str, str]]
) -> pd.DataFrame:

    vulnerability_count = 0
    seen_vulnerabilities = set()

    rows = []

    for image_name, data in iter_scans:
        for result in data.get("Results", []):
            for vulnerability in result.get("Vulnerabilities", []):
                vuln_id = vulnerability.get("VulnerabilityID", "N/A")
                unique_vulnerability_key = (vuln_id, image_name)
                image_ref = image_name.split(":")[0]

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

                cveId = vulnerability.get("VulnerabilityID")

                if not cveId:
                    continue

                exception = exceptions.get(cveId)

                if exception:
                    if image_ref in exception:
                        rational = exception[image_ref]
                    else:
                        most_common = pd.Series(exception).value_counts()\
                            .sort_values(ascending=False).head(1).index[0]
                        rational = f"(Possible) {most_common}"

                    out_dict = {
                        "Relevant to Product?": "No",
                        "Reason": rational,
                    }
                else:

                    can_be_remediated = "Yes" if cveId in actions and image_ref in actions[cveId] else "No"
                    action_plan = actions[cveId][image_ref] if can_be_remediated=="Yes" else ""

                    out_dict = {
                        "Relevant to Product?": "Yes",
                        "Patchable": can_be_remediated,
                        "Ticket": action_plan
                    }

                rows.append({
                    "CVE": cveId,
                    "Package Name": vulnerability.get("PkgName", "N/A"),
                    "Version": vulnerability.get("InstalledVersion", "N/A"),
                    "Is KEV?": is_kev,
                    "Severity": vulnerability.get("Severity", "N/A").capitalize(),
                    "NVD/CVSS Score": vulnerability.get("CVSS", {}).get("nvd", {}).get("V3Score", "N/A"),
                    "Upstream presence": ("Yes" if cveId in upstream_vulns else "No") if upstream_vulns else "N/A",
                    "Patch version": fixed_version if patch_exists else "N/A",
                    "Patch produced by Canonical": ("Yes" if "ubuntu" in fixed_version else "No") if patch_exists else "N/A",
                    "Vulnerability Name": vulnerability.get("Title", "N/A"),
                    "Description": vulnerability.get("Description", "N/A").replace("\r", "\n"),
                    "Affected Component": image_name,
                } | out_dict)


    logger.info(f"Found {vulnerability_count} vulnerabilities")

    return pd.DataFrame.from_records(rows)

def read_tickets(filename: str):
    try:
        actions_df = pd.read_excel(filename, index_col=[0, 1])
    except FileNotFoundError:
        return pd.Series()
    tickets = actions_df.reset_index().set_index(["CVE", "Image"])[["Ticket"]].sort_index()

    # Output as nested dictionary
    return tickets.groupby(level=0).apply(lambda df: df.xs(df.name)["Ticket"].to_dict()).to_dict()

# We also want to merge CVEs, so only one entry exists for each CVE
def merge_cve(input_df: pd.DataFrame):
    """Merge CVEs with same ID on different images"""

    def reduce(subset: pd.DataFrame):
        components = ",".join(subset["Affected Component"].values)
        tickets = ",".join({ticket
            for ticket in subset["Ticket"].values
            if ticket and isinstance(ticket, str)
        })
        row = subset.iloc[0].copy(deep=True)
        row["Affected Component"] = components
        row["Ticket"] = tickets
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
    parser.add_argument(
        "--upstream-images",
        dest="UPSTREAM",
        type=str,
        default=None,
        help="The path to the input text file containing image paths.",
    )
    parser.add_argument(
        "--tickets",
        dest="TICKETS",
        type=str,
        default=None,
        help="The path to the input file containing tickets and their relations to CVEs.",
        # https://docs.google.com/spreadsheets/d/1jBoL3Itc2SEgJdukd4rASOd01r9vXhRv/edit?usp=drive_link&ouid=106637444762362243511&rtpof=true&sd=true
    )
    parser.add_argument(
        "--exceptions",
        dest="EXCEPTIONS",
        type=str,
        default=EXCEPTION_FILE,
        help="The path to the input file containing the list of known exceptions.",
        # https://docs.google.com/spreadsheets/d/1wIPrpKPdm4QVR0XyOtPRkAWU0kqLUb2x/edit?usp=drive_link&ouid=106637444762362243511&rtpof=true&sd=true
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

    upstream_cves = get_upstream_cves(iter_reports(args.UPSTREAM)) if args.UPSTREAM else None

    if args.TICKETS:
        actions = read_tickets(args.TICKETS)
    else:
        actions = {}

    cve_list = scan_images(
        data, get_kves(Path(KEV_FILE)), get_exceptions(Path(args.EXCEPTIONS)),
        upstream_cves, actions
    )

    if severities:
        cve_list = cve_list[cve_list["Severity"].isin(list(severities))]
    
    merged_list = merge_cve(cve_list)

    with pd.ExcelWriter(REPORT_CSV_FILE) as writer:
        merged_list.to_excel(writer, sheet_name="All Vulnerabilities")
        merged_list[(merged_list["Severity"]=="Critical") + (merged_list["Is KEV?"]=="Yes")].to_excel(writer, sheet_name="Criticals & KEVs")
