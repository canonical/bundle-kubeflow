# Kubeflow Operators

## Introduction

Charmed Kubeflow is a full set of Kubernetes operators to deliver the 30+ applications and services
that make up the latest version of Kubeflow, for easy operations anywhere, from workstations to
on-prem, to public cloud and edge.

A charm is a software package that includes an operator together with metadata that supports the
integration of many operators in a coherent aggregated system.

This technology leverages the Juju Operator Lifecycle Manager to provide day-0 to day-2 operations
of Kubeflow.

Visit [charmed-kubeflow.io][charmedkf] for more information.

## Install


For any Kubernetes, follow the [installation instructions][install].

## Testing

To deploy this bundle and run tests locally, do the following:

1. Set up Kubernetes, Juju, and deploy the bundle you're interested in (`kubeflow` or
   `kubeflow-lite`) using the [installation guide](https://charmed-kubeflow.io/docs/install/). This
   must include populating the `.kube/config` file with your Kubernetes cluster as the active
   context. Do not create a namespace with the same name as the username, this will cause 
   pipelines tests to fail. Beware of using `admin` as the dex-auth static-username as the tests 
   attempt to create a profile and `admin` conflicts with an existing default profile.
1. Install test prerequisites:

   ```bash
   sudo snap install juju-wait --classic
   sudo snap install juju-kubectl --classic
   sudo snap install charmcraft --classic
   sudo apt update
   sudo apt install -y libssl-dev firefox-geckodriver
   sudo pip3 install tox
   sudo pip3 install -r requirements.txt
   ```

1. Run tests on your bundle with tox. As many tests need authentication, make sure you pass the
   username and password you set in step (1) through environment variable or argument, for example:
   - full bundle (using command line arguments):
      ```
      tox -e tests -- -m full --username user123@email.com --password user123
      ```
   - lite bundle (using environment variables):
      ```
      export KUBEFLOW_AUTH_USERNAME=user1234@email.com
      export KUBEFLOW_AUTH_PASSWORD=user1234
      tox -e tests -- -m lite
      ```

Subsets of the tests are also available using pytest's substring expression selector (e.g.:
`tox -e tests -- -m full --username user123@email.com --password user123 -k 'selenium'` to run just
the selenium tests).

## Documentation

Read the [official documentation][docs].

[charmedkf]: https://charmed-kubeflow.io/
[docs]: https://charmed-kubeflow.io/docs/
[install]: https://charmed-kubeflow.io/docs/install
