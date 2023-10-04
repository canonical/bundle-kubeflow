# Get bundle test path for specific release
import os
import sys

# For new releases, add a release/tests mapping to this dictionary
RELEASE_TESTS = {
    "1.6/beta": "./tests-bundle/1.6/",
    "1.6/edge": "./tests-bundle/1.6/",
    "1.6/stable": "./tests-bundle/1.6/",
    "1.7/beta": "./tests-bundle/1.7/",
    "1.7/edge": "./tests-bundle/1.7/",
    "1.7/stable": "./tests-bundle/1.7/",
    "1.8/beta": "./tests-bundle/1.8/",
    "1.8/edge": "./tests-bundle/1.8/",
    "1.8/stable": "./tests-bundle/1.8/",
    "latest/beta": "./tests-bundle/1.7/",
    "latest/edge": "./tests-bundle/1.7/",
}


def get_bundle_test_path_from_release() -> None:
    if len(sys.argv) <= 1:
        raise Exception("No release given as input.")

    release = sys.argv[1]

    if release not in RELEASE_TESTS.keys():
        raise Exception(
            f"No tests available for {release} release. Please proceed to manually publish to Charmhub if needed."
        )
    bundle_test_path = RELEASE_TESTS[release]

    # Check if file in bundle_test_path output exists
    # Expect the script to be executed from `bundle-kubeflow` repo directory
    if os.path.exists(bundle_test_path):
        print(f"Returning bundle_test_path={bundle_test_path}")
        with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
            print(f'bundle_test_path={bundle_test_path}', file=fh)
    else:
        raise Exception(f"There is no directory in path: {bundle_test_path}")


get_bundle_test_path_from_release()
