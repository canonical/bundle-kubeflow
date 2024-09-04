import os
import sys
import json

# Parse the versions given as a comma-separated list and return a JSON array
def parse_versions(input_versions):
    # Default version string if the input is empty
    if not input_versions:
        input_versions = "1.8,1.9,latest"
    else:
        # Remove whitespace between entries
        input_versions = input_versions.replace(" ", "")
    
    # Convert to JSON array
    json_array = json.dumps(input_versions.split(","))
    return json_array

if __name__ == "__main__":
    # Read the input of the Github Action from the environment variable
    input_versions = os.getenv('INPUT_BUNDLE_VERSION', '')
    json_array = parse_versions(input_versions)
    print(f"bundle_versions={json_array}")
    with open(os.environ['GITHUB_OUTPUT'], 'a') as output_file:
        output_file.write(f"bundle_versions={json_array}\n")

