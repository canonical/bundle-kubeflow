# Generate vulnerabilities for Charmed Kubeflow

This subdirectory contains scripts that automatically generate `.csv` files of the vulnerabilities that exist in the images used by Charmed Kubeflow. There are 2 scripts in this subdirectory:
- `produce_report.py` 
- `find_severe_cves.py`

## Prerequisites

- A working Python installation
- `trivy` which is a security scanner used to scan the images. The binary can be installed on Ubuntu systems with `sudo apt install trivy`. View the [GitHub page](https://github.com/aquasecurity/trivy) for more information.
- A file named `known_exploited_vulnerabilities.csv` that contains known exploited vulnerabilities (KEVs). This file can be downloaded from the [CISA website](https://www.cisa.gov/known-exploited-vulnerabilities-catalog).
- An `images.txt` file with the images to scan. Each line should contain an image tag. This file can be conveniently generated using the [get_all_images.py](https://github.com/canonical/bundle-kubeflow/tree/main/scripts#gather-images-used-by-a-bundle) script in this repository.

## How to run

First, create a Python virtual environment with `venv`:
```shell
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Then, run the 2 scripts in order:

```shell
# Create `vulnerability_report.csv`
python3 produce_report.py images.txt
# Find the severe CVEs with the file produced above
python3 find_severe_cves.py vulnerability_report.csv
```

When ran for the first time, the script has to pull each one of the specified images before scanning, which may take around 20 minutes in total.

The `produce_report.py` script can also take as input a folder where the trivy reports for all images are already stored. To do so, provide the 
path to the folder where the JSON are stored, and change the type of the input using the `--type folder_reports` argument, e.g. 

```shell
python3 produce_report.py path/to/the/folder --type folder_reports
```

When creating the report, only certain severities can be selected by using the `--severity` command line argument, e.g.

```
python3 produce_report.py --severity High,Low --severity Critical
```

Note that the severity can be fed into multiple case format, e.g.

```
python3 produce_report.py --severity High,LOW --severity critical --severity high
```

are all valid options.

Running the script above will generate the following 2 files:
- `vulnerability_report.csv` with all CVEs per image
- `severe_cves.csv` with all "severe" CVEs grouped by ID. "Severe" CVEs are "High" or "Critical" CVEs that don't have fixed versions.


### Exceptions and Actions

In the RAF review process, the Security team asked for further information in the CVE export, specifically:

* Vulnerability applicability to Kubeflow (whether there are exceptions for which those CVEs would not apply)
* To refer to the tickets when the CVE would be fixed by some development work we have in our backlog.

To get these pieces of information we therefore need to integrate the CVE export with two sources of data (that have also been uploaded to Google Drive):

* [exceptions list](https://docs.google.com/spreadsheets/d/1wIPrpKPdm4QVR0XyOtPRkAWU0kqLUb2x/edit?usp=drive_link&ouid=106637444762362243511&rtpof=true&sd=true)
* [Jira tickets addressing CVEs](https://docs.google.com/spreadsheets/d/1jBoL3Itc2SEgJdukd4rASOd01r9vXhRv/edit?usp=drive_link&ouid=106637444762362243511&rtpof=true&sd=true)

