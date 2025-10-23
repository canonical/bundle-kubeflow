# Generate vulnerabilities for Charmed Kubeflow

This subdirectory contains scripts that automatically generate `.csv` files of the vulnerabilities that exist in the images used by Charmed Kubeflow. There are 2 scripts here:
- `produce_report.py` 
- `find_severe_cves.py`

## How to run

Simply run the 2 scripts in order:

```shell
python3 produce_report.py
python3 find_severe_cves.py
```

The following 3 files will be generated:
- `vulnerability_report.csv` with all CVEs per images
- `vulnerability_report_merged.csv` with all CVEs grouped by CVE ID
- `severe_cves.csv` with all "severe" CVEs grouped by ID. "Severe" CVEs are "High" or "Critical" CVEs that don't have fixed versions.

## Notes

- These scripts use `trivy` for scanning images  At the time of scanning, version `0.66` of `trivy` was used.
