import os
import sys
import json

# Parse the versions given as a comma-separated list and return a JSON array
def parse_versions(input_versions):
    # Remove whitespace between entries
    input_versions = input_versions.replace(" ", "")
    
    # Convert to JSON array
    json_array = json.dumps(input_versions.split(","))
    return json_array

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "":
        raise Exception("No bundle versions given as input.")
    
    input_versions = sys.argv[1]
    json_array = parse_versions(input_versions)
    print(f"bundle_versions={json_array}")

    with open(os.environ['GITHUB_OUTPUT'], 'a') as output_file:
        output_file.write(f"bundle_versions={json_array}\n")

