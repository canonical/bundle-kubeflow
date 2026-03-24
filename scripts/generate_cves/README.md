# Generate vulnerabilities for Charmed Kubeflow

This directory contains scripts to produce reports of the vulnerabilities that exist in the images used by Charmed Kubeflow:
- `create_trivy_reports.py`
- `produce_report.py` 

## Prerequisites

- A working Python installation
- `trivy` which is a security scanner used to scan the images. The binary can be installed on Ubuntu systems with `sudo apt install trivy`. View the [GitHub page](https://github.com/aquasecurity/trivy) for more information.
- A CSV file containing Known Exploited Vulnerabilities (KEVs). This file can be downloaded from the [CISA website](https://www.cisa.gov/known-exploited-vulnerabilities-catalog).
- An `images.txt` file with the images to scan. Each line should contain an image tag. This file can be conveniently generated using the [get_all_images.py](https://github.com/canonical/bundle-kubeflow/tree/main/scripts#gather-images-used-by-a-bundle) script in this repository.

## How to run

First, create a Python virtual environment with `venv`:
```shell
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

To create all Trivy reports for the images, run:
```
./create_trivy_reports.py images.txt
```

The default output directory is `trivy-reports`. You can also specify the output directory with the `-o` option.

Then, run the `produce_report.py` script to produce the vulnerability report. You can pass either:
- A directory of Trivy JSON reports, or
- A text file containing a list of images (one per line).

```shell
# Using a directory of Trivy reports
python produce_report.py trivy-reports --kev-file known_exploited_vulnerabilities.csv

# Using a list of images (the script will scan them with Trivy)
python produce_vulnerability_report.py images.txt --kev-file known_exploited_vulnerabilities.csv
```

When creating the report, only certain severities can be selected by using the `--severity` command line argument, e.g.

```
python3 produce_report.py trivy-reports \
  --kev-file known_exploited_vulnerabilities.csv \
  --severity High,Low \
  --severity Critical
```

Note that the severity can be fed into multiple case format, e.g.

```
python3 produce_vulnerability_report.py trivy-reports \
  --kev-file known_exploited_vulnerabilities.csv \
  --severity High,LOW \
  --severity critical \
  --severity high
```

are all valid options.

Running the script above will generate the following a file named `Vulnerability_Tracker-Charmed_Kubeflow.xlsx` with 2 sheets:
- `All Vulnerabilities` with all CVEs per image
- `Critical, High & KEV` with all CVEs that are "High", "Critical", or are part of KEVs.

## CLI reference

`produce_report.py` usage:

```
python produce_report.py INPUT_PATH [options]
```

### Positional argument

- `INPUT_PATH`  
  Path to either:
  - A text file containing image references (one per line), or  
  - A directory containing Trivy JSON reports.

### Optional arguments

- `--kev-file <path>`  
  Path to the CSV file containing Known Exploited Vulnerabilities (KEVs).  
  Default: `known_exploited_vulnerabilities.csv`

- `--severity <levels>`  
  Filter by severity. Can be provided multiple times and/or as comma-separated values.  
  Valid values: `Low`, `Medium`, `High`, `Critical` (case-insensitive).

- `--upstream-path <path>`  
  Path to a directory of Trivy JSON reports representing upstream images.  
  Used to determine whether a CVE is also present upstream.

- `--tickets <path>`  
  Path to an Excel file mapping CVEs and images to internal tracking tickets.

- `--exceptions <path>`  
  Path to an Excel file listing CVE exceptions (non-applicable vulnerabilities).  
  Default: `CVE_Exceptions.xlsx`


### Exceptions and Actions

In the RAF review process, the Security team asked for further information in the CVE export, specifically:

* Vulnerability applicability to Kubeflow (whether there are exceptions for which those CVEs would not apply)
* To refer to the tickets when the CVE would be fixed by some development work we have in our backlog.

To get these pieces of information we therefore need to integrate the CVE export with two sources of data (that have also been uploaded to Google Drive):

* [exceptions list](https://docs.google.com/spreadsheets/d/1wIPrpKPdm4QVR0XyOtPRkAWU0kqLUb2x/edit?usp=drive_link&ouid=106637444762362243511&rtpof=true&sd=true)
* [Jira tickets addressing CVEs](https://docs.google.com/spreadsheets/d/1jBoL3Itc2SEgJdukd4rASOd01r9vXhRv/edit?usp=drive_link&ouid=106637444762362243511&rtpof=true&sd=true)
