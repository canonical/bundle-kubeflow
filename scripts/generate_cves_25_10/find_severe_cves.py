import csv

# For the purposes of this script, severe CVES are considered CVEs that are
# (KEV or High or Critical )and unfixable

INPUT_CSV_FILE = "vulnerability_report_merged.csv"
OUTPUT_CSV_FILE = "severe_cves.csv"

def find_critical_cves(input_csv_file, output_csv_file):
    """Open a CSV file and """
    critical_counter = 0
    critical_unfixed_counter = 0
    critical_unfixed_rows = []

    critical_images = set()
    
    with open(input_csv_file, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames
        for row in reader:
            if row.get("Is KEV?") == "Yes" or row.get("Severity") == "High" or row.get("Severity") == "Critical":
                critical_counter += 1
                
                if row.get("Can it be remediated?") == "No":
                    critical_unfixed_counter += 1
                    critical_unfixed_rows.append(row)

                    components = [comp.strip() for comp in row.get("Affected Component").split(',')]
                    for component in components:
                        critical_images.add(component)

                    
    print(f"There are {critical_counter} critical vulnerabilities, of which {critical_unfixed_counter} cannot be remediated")

    if critical_unfixed_rows:
        with open(output_csv_file, "w", newline="", encoding="utf-8") as outfile:
            # Use the original headers for the new file
            writer = csv.DictWriter(outfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(critical_unfixed_rows)
        print(f"Successfully wrote {critical_unfixed_counter} unfixed vulnerabilities to {output_csv_file}")
    else:
        print("No unfixed critical/high vulnerabilities found to write.")

    for image in critical_images:
        print(image)
    
if __name__ == "__main__":
    find_critical_cves(INPUT_CSV_FILE, OUTPUT_CSV_FILE)
