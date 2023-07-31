# Charmed Kubeflow Automated UATs

Automated User Acceptance Tests (UATs) are essential for evaluating the stability of Charmed
Kubeflow, as well as catching issues early, and are intended to be an invaluable testing tool both
pre-release and post-installation. They combine different components of Charmed Kubeflow in a way
that gives us confidence that everything works as expected, and are meant to be used by end-users
as well as developers alike.

## Design

Charmed Kubeflow UATs are broken down in test scenarios implemented as Python notebooks, which are
easy to share, understand, and maintain. The following workflows are supported:
* Users can run the tests:
  * from inside a Charmed Kubeflow cluster, e.g. running the test suite included in `tests` inside
    a Notebook
  * from a machine with access to a Charmed Kubeflow cluster, using the `driver`
* Charmed Kubeflow CI can run the tests from Github Workflows, using the `driver`

More specifically, the provided `tests` directory is **standalone**. Users can clone this repo
inside a Jupyter Notebook and run the test suite with `pytest`, as a way to verify their
deployments and familiarise themselves with different Charmed Kubeflow features.

On the other hand, the provided `driver` allows us to automate the test execution on an existing
cluster using `pytest` and a Kubernetes Job. More details on how to run the tests can be found in
the [Run the tests](#run-the-tests) section.

## Prerequisites

Executing the UATs requires a deployed Kubeflow cluster. That said, the deployment and
configuration steps are outside the scope of this project. In other words, the automated tests are
going to assume programmatic access to a Kubeflow installation. Such a deployment consists (at the
very least) of the following pieces:

* A **Kubernetes cluster**, e.g.
    * MicroK8s
    * Charmed Kubernetes
    * EKS cluster
* **Charmed Kubeflow** deployed on top of it
* **MLFlow (optional)** deployed alongside Kubeflow

For instructions on deploying and getting started with Charmed Kubeflow, we recommend that you
start with [this guide](https://charmed-kubeflow.io/docs/get-started-with-charmed-kubeflow).

The UATs include tests that assume MLFlow is installed alongside Kubeflow, which will otherwise
fail. For instructions on deploying MLFlow you can start with [this
guide](https://discourse.charmhub.io/t/deploying-charmed-mlflow-v2-and-kubeflow-to-eks/10973),
ignoring the EKS specific steps.

## Run the tests

As mentioned before, when it comes to running the tests, you've got 2 options:
* Running the `tests` suite directly with `pytest` inside a Jupyter Notebook
* Running the tests on an existing cluster using the `driver` along with the provided automation

### Running inside a Notebook

* Create a new Notebook using the `jupyter-scipy` image:
   * Navigate to `Advanced options` > `Configurations`
   * Select all available configurations in order for Kubeflow integrations to work as expected
   * Launch the Notebook and wait for it to be created
* Start a new terminal session and clone this repo locally:

   ```bash
   git clone https://github.com/canonical/charmed-kubeflow-uats.git
   ```
* Navigate to the `tests` directory:

   ```bash
   cd charmed-kubeflow-uats/tests
   ```
* Follow the instructions of the provided [README.md](tests/README.md) to execute the test suite
  with `pytest`

### Running from a configured management enviroment using the `driver`

Any enviroment that can be used to access and configure the Charmed Kubeflow deployment is
considered a configured management environment. That is, essentially, any machine with `kubectl`
access to the underlying Kubernetes cluster. This is crucial, since the driver directly depends on
a Kubernetes Job to run the tests. More specifically, the `driver` executes the following steps:
1. Create a Kubeflow Profile (i.e. `test-kubeflow`) to run the tests in
2. Submit a Kubernetes Job (i.e. `test-kubeflow`) that runs `tests`
   The Job performs the following:
   * Mount the local `tests` directory to a Pod that uses `jupyter-scipy` as the container image
   * Install python dependencies specified in the [requirements.txt](tests/requirements.txt)
   * Run the test suite by executing `pytest`
3. Wait until the Job completes (regardless of the outcome)
4. Collect and report its logs, corresponding to the `pytest` execution of `tests`
5. Cleanup (remove created Job and Profile)

#### Limitations

With the current implementation we have to wait until the Job completes to fetch its logs. Of
course this makes for a suboptimal UX, since the user might have to wait long before they learn
about the outcome of their tests. Ideally, the Job logs should be streamed directly to the `pytest`
output, providing real-time insight. This is a known limitation that will be addressed in a future
iteration.
