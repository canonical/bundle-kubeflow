import os
import sys
import json

def parse_versions(input_versions):
    # Default version string if input is empty
    if not input_versions:
        input_versions = "1.8,1.9,latest"
    else:
        # Remove whitespace between entries
        input_versions = input_versions.replace(" ", "")
    
    # Convert to JSON array
    json_array = json.dumps(input_versions.split(","))
    return json_array

if __name__ == "__main__":
    # Read the input version from the environment variable
    input_versions = os.getenv('INPUT_BUNDLE_VERSION', '')
    # Parse the versions
    json_array = parse_versions(input_versions)
    # Output the result to GitHub Actions
    print(f"bundle_versions={json_array}")
    # Write to GitHub Actions output
    with open(os.environ['GITHUB_OUTPUT'], 'a') as output_file:
        output_file.write(f"bundle_versions={json_array}\n")

