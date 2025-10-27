# Generate vulnerabilities for Charmed Kubeflow

This subdirectory contains scripts that automatically generate `.csv` files of the vulnerabilities that exist in the images used by Charmed Kubeflow. There are 2 scripts in this subdirectory:
- `produce_report.py` 
- `find_severe_cves.py`

## How to run

Simply run the 2 scripts in order:

```shell
python3 produce_report.py images.txt.20251003
# Find the severe CVEs with the file produced above
python3 find_severe_cves.py vulnerability_report_merged.csv
```

The following 3 files will be generated:
- `vulnerability_report.csv` with all CVEs per image
- `vulnerability_report_merged.csv` with all CVEs grouped by CVE ID
- `severe_cves.csv` with all "severe" CVEs grouped by ID. "Severe" CVEs are "High" or "Critical" CVEs that don't have fixed versions.

## Notes

- These scripts use `trivy` for scanning images. At the time of scanning (2025-10-21), version `0.66` of `trivy` was used.
- A file named `known_exploited_vulnerabilities.csv` that contains known exploited vulnerabilities is required. This file can be downloaded from the [CISA website](https://www.cisa.gov/known-exploited-vulnerabilities-catalog).
