# Test Kubeflow Integrations

Run Python notebooks with Pytest inside a Notebook Server to verify the integration of Kubeflow
with different components. The notebook tests are stored in the `notebooks/` directory.

These are regular Python notebooks, which you can view and run manually without any modifications.
They perform simple tasks using the respective APIs and programmatically verify the results.

## Setup

Before running the tests, make sure that the [required Python dependencies](requirements.txt) are
installed:

```
pip install -r requirements.txt
```

## Run

You can execute the full Pytest suite by running:

```
pytest
```

The above inherits the configuration set in [pytest.ini](pytest.ini). Feel free to provide any
required extra settings either using that file or directly through CLI arguments.
