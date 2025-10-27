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
# Create `vulnerability_report.csv` and `vulnerability_report_merged.csv`
python3 produce_report.py images.txt
# Find the severe CVEs with the file produced above
python3 find_severe_cves.py vulnerability_report_merged.csv
```

When ran for the first time, the script has to pull each one of the specified images before scanning, which may take around 20 minutes in total.

The following 3 files will be generated:
- `vulnerability_report.csv` with all CVEs per image
- `vulnerability_report_merged.csv` with all CVEs grouped by CVE ID
- `severe_cves.csv` with all "severe" CVEs grouped by ID. "Severe" CVEs are "High" or "Critical" CVEs that don't have fixed versions.
