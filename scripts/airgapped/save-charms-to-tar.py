import argparse
import logging
import subprocess

import os
import yaml

import utils as airgap_utils

log = logging.getLogger(__name__)


def download_bundle_charms(bundle: dict, no_zip: bool,
                           skip_resource_dispatcher: bool,
                           output_tar: str) -> None:
    """Given a bundle dict download all the charms using juju download."""

    log.info("Downloading all charms...")
    applications = bundle.get("applications")
    for app in applications.values():
        subprocess.run(["juju", "download", "--channel", app["channel"],
                        app["charm"]])

    # FIXME: https://github.com/canonical/bundle-kubeflow/issues/789
    if not skip_resource_dispatcher:
        log.info("Fetching charm of resource-dispatcher.")
        subprocess.run(["juju", "download", "--channel", "1.0/stable",
                        "resource-dispatcher"])

    if not no_zip:
        # python3 download_bundle_charms.py $BUNDLE_PATH --zip_all
        log.info("Creating the tar with all the charms...")
        cmd = "tar -cv --use-compress-program=pigz -f %s *.charm" % output_tar
        subprocess.run(cmd, shell=True)
        log.info("Created %s file will all charms.", output_tar)

        log.info("Removing downloaded charms...")
        airgap_utils.delete_files_with_extension(os.getcwd(), ".charm")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bundle Charms Downloader")
    parser.add_argument("--no-zip", action="store_true")
    parser.add_argument("--skip-resource-dispatcher", action="store_true")
    parser.add_argument("--output-tar", default="charms.tar.gz")
    parser.add_argument("bundle")
    args = parser.parse_args()
    log.info(args.no_zip)

    bundle_dict = {}
    with open(args.bundle, 'r') as file:
        bundle_dict = yaml.safe_load(file)

    airgap_utils.delete_file_if_exists(args.output_tar)
    download_bundle_charms(bundle_dict, args.no_zip,
                           args.skip_resource_dispatcher,
                           args.output_tar)
