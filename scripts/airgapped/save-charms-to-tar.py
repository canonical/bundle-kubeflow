import argparse
import logging
import subprocess

import yaml

from utils import delete_file_if_exists

log = logging.getLogger(__name__)


def download_bundle_charms(bundle: dict, zip_all: bool,
                           delete_afterwards: bool,
                           resource_dispatcher: bool) -> None:
    """Given a bundle dict download all the charms using juju download."""

    log.info("Downloading all charms...")
    applications = bundle.get("applications")
    for app in applications.values():
        subprocess.run(["juju", "download", "--channel", app["channel"],
                        app["charm"]])

    if resource_dispatcher:
        log.info("Fetching charm of resource-dispatcher.")
        subprocess.run(["juju", "download", "--channel", "1.0/stable",
                        "resource-dispatcher"])

    if zip_all:
        # python3 download_bundle_charms.py $BUNDLE_PATH --zip_all
        # --delete_afterwards
        log.info("Creating the tar with all the charms...")
        cmd = "tar -cv --use-compress-program=pigz -f charms.tar.gz *.charm"
        subprocess.run(cmd, shell=True)
        log.info("Created charms.tar.gz file will all charms.")

    if delete_afterwards:
        log.info("Removing downloaded charms...")
        command = "rm -f *.charm"
        subprocess.run(command, shell=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bundle Charms Downloader")
    parser.add_argument("--zip-all", action="store_false")
    parser.add_argument("--delete-afterwards", action="store_false")
    parser.add_argument("--resource-dispatcher", action="store_false")
    parser.add_argument("bundle")
    args = parser.parse_args()

    bundle_dict = {}
    with open(args.bundle, 'r') as file:
        bundle_dict = yaml.safe_load(file)

    delete_file_if_exists("charms.tar.gz")
    download_bundle_charms(bundle_dict, args.zip_all, args.delete_afterwards,
                           args.resource_dispatcher)
