# Get bundle path for specific release
import re
import sys
import os


def get_bundle_path_from_release() -> None:
    if len(sys.argv) > 1:
        release = sys.argv[1]
        bundle_is_latest = re.search("^latest/", release)
        if bundle_is_latest:
            bundle_path = "./releases/" + release + "/"
        else:
            bundle_path = "./releases/" + release + "/kubeflow/"

        # Check if file in bundle_path output exists
        # Expect the script to be executed from `bundle-kubeflow` repo directory
        if os.path.exists(bundle_path):
            print(f"Returning bundle_path={bundle_path}")
            with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
                print(f'bundle_path={bundle_path}', file=fh)
        else:
            raise Exception(f"There is no file in path: {bundle_path}")
    else:
        raise Exception("No release given as input.")


get_bundle_path_from_release()
