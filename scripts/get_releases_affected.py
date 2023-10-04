# Extract from the files changed by this PR the releases/channels affected.
import json
import os
import re
import sys

ACCEPTED_TRACKS = ["1.7", "1.8", "latest"]
ACCEPTED_RISKS = ["beta", "edge", "stable"]


def get_releases_affected() -> None:
    releases_affected = set()

    for file_path in sys.argv:
        # check if string starts with the "releases"
        file_path_starts_with_releases = re.search("^releases", file_path)

        if file_path_starts_with_releases:
            directories = file_path.split('/')
            track = directories[1]
            risk = directories[2]

            if(track in ACCEPTED_TRACKS and risk in ACCEPTED_RISKS):
                release = f"{track}/{risk}"
                releases_affected.add(release)
            else:
                raise Exception(
                    f"File {file_path} was changed in 'releases' directory but it's not part of a known release/channel.")

    releases_affected_json = json.dumps(list(releases_affected))
    print(
        f"The following releases have been affected by this PR: {releases_affected_json}")
    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        print(f'releases_affected_json={releases_affected_json}', file=fh)


get_releases_affected()
