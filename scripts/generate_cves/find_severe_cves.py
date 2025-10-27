import argparse
import csv
import logging
import sys

# For the purposes of this script, severe CVES are considered CVEs that are
# (KEV or High or Critical) and unfixable

LOG_FORMAT = "%(levelname)s:%(name)s: %(message)s"
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

OUTPUT_CSV_FILE = "severe_cves.csv"


def find_critical_cves(input_csv_file, output_csv_file):
    """Open a CSV file and produce a new one with all severe (KEV, High or Critical) vulnerabilities."""
    critical_counter = 0
    critical_unfixed_counter = 0
    critical_unfixed_rows = []

    with open(input_csv_file, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames
        for row in reader:
            if (
                row.get("Is KEV?") == "Yes"
                or row.get("Severity") == "High"
                or row.get("Severity") == "Critical"
            ):
                critical_counter += 1

                if row.get("Can it be remediated?") == "No":
                    critical_unfixed_counter += 1
                    critical_unfixed_rows.append(row)

    logger.info(
        f"There are {critical_counter} critical vulnerabilities, of which {critical_unfixed_counter} cannot be remediated"
    )

    if critical_unfixed_rows:
        with open(output_csv_file, "w", newline="", encoding="utf-8") as outfile:
            # Use the original headers for the new file
            writer = csv.DictWriter(outfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(critical_unfixed_rows)
        logger.info(
            f"Successfully wrote {critical_unfixed_counter} unfixed vulnerabilities to {output_csv_file}"
        )
    else:
        logger.info("No unfixed critical/high vulnerabilities found to write.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "INPUT_CSV_FILE",
        type=str,
        help="The path to the input .csv file container the vulnerability report.",
    )
    args = parser.parse_args()
    find_critical_cves(args.INPUT_CSV_FILE, OUTPUT_CSV_FILE)
