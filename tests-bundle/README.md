# Tests Bundle

This folder contains the full bundle tests for Kubeflow. These tests are designed to deploy Kubeflow and run various tests on the deployed Kubeflow, including Selenium tests for interacting with the Kubeflow UI. The long-term vision for this bundle is to add hundreds of tests to thoroughly test the entire Kubeflow bundle before deployment.

## Test Structure

The tests are organized into directories based on the version of Kubeflow. Each version has its own suite of tests, although there may be similarities between versions. Minimally, each version's directory contains a Python file for deploying Kubeflow and one or more other files representing other tests.

The test order is enforced to ensure that the deployment test runs and succeeds before further tests can run. This order is defined with the help of pytest markers, where the "deploy" tests are executed first.

## How to Run the Tests as a GitHub Action

To run the tests as a GitHub Action, follow these steps:

1. Trigger the full bundle tests GitHub action (Tests) by clicking "Run workflow" in the repository.
2. Provide the following inputs:

   - **Folder**: Path from the content root to the directory for the version of Kubeflow you want to test. 

   - **TOX Posargs**: The deployment source for `juju deploy`. This will either be a published channel e.g. `--channel=1.7/stable` or the path from the content root of an unpublished `bundle.yaml` file within the repo.

3. The GitHub action will start executing and perform the following steps:

   - Set up the prerequisite installation and configuration for Kubeflow, including microk8s and Juju.
   - Run the bundle tests, which are Python tests, to deploy Kubeflow and perform further tests on the deployed Kubeflow.
   - Perform post-processing of the test results and gather information in case of failures.

Please refer to the GitHub Action YAML file in the parent repository for more detailed information on the action setup and configuration.

Note: This README assumes that you are familiar with GitHub Actions and have the necessary permissions to trigger and run actions in the repository.
