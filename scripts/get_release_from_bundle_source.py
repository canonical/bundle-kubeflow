# Get bundle test path for specific release
import os
import re
import sys

def get_release_from_bundle_source() -> None:
    if len(sys.argv) <= 1:
        raise Exception("No bundle source given as input.")

    bundle_source = sys.argv[1]
    # Bundle source input should be `--channel <channel_name>` or `--file <bundle_file>.yaml``
    # e.g. --channel 1.10/stable or --file releases/1.10/stable/kubeflow/bundle.yaml
    bundle_source_starts_with_channel = re.search("^--channel", bundle_source)
    bundle_source_starts_with_file = re.search("^--file", bundle_source)

    try:
        if bundle_source_starts_with_channel:
            if re.search("^--channel=", bundle_source):
                substrings = bundle_source.split("=")
            else:
                substrings = bundle_source.split(" ")
            release=substrings[1]
        elif bundle_source_starts_with_file:
            substrings = bundle_source.split('/')
            track = substrings[1]
            risk = substrings[2]
            release = f"{track}/{risk}"
        print(
            f"Returning release={release}.")
    except:
        raise Exception("Bundle source doesn't have expected format.")

    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        print(f'release={release}', file=fh)

get_release_from_bundle_source()
