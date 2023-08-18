# Get bundle test path for specific release
import re
import sys
import os


def get_bundle_test_path_from_release() -> None:
    if len(sys.argv) > 1:
        release = sys.argv[1]
        bundle_is_1_6 = re.search("^1.6/", release)
        bundle_is_1_4 = re.search("^1.4/", release)
        if bundle_is_1_4:
            raise Exception(
                f"No tests available for 1.4 release. Please proceed to manually publish to Charmhub if needed."
            )
        elif bundle_is_1_6:
            bundle_test_path = "./tests-bundle/1.6/"
        else:
            bundle_test_path = "./tests-bundle/1.7/"

        # Check if file in bundle_test_path output exists
        # Expect the script to be executed from `bundle-kubeflow` repo directory
        if os.path.exists(bundle_test_path):
            print(f"Returning bundle_test_path={bundle_test_path}")
            with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
                print(f'bundle_test_path={bundle_test_path}', file=fh)
        else:
            raise Exception(f"There is no directory in path: {bundle_test_path}")
    else:
        raise Exception("No release given as input.")


get_bundle_test_path_from_release()
