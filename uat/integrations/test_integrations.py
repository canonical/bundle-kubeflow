# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
import os

import nbformat
import pytest
from nbclient.exceptions import CellExecutionError
from nbconvert.preprocessors import ExecutePreprocessor

# get the current working directory
current_directory = os.getcwd()

# change the working directory to the "examples" directory
EXAMPLES_DIR = "examples"
examples_directory = os.path.join(current_directory, EXAMPLES_DIR)
os.chdir(examples_directory)

KATIB_INTEGRATION = {"path": "katib-integration.ipynb", "id": "katib"}
KFP_INTEGRATION = {"path": "kfp-integration.ipynb", "id": "kfp"}
MINIO_INTEGRATION = {"path": "minio-integration.ipynb", "id": "minio"}
MLFLOW_INTEGRATION = {"path": "mlflow-integration.ipynb", "id": "mlflow"}

log = logging.getLogger(__name__)


def format_error_message(traceback: list):
    """Format error message."""
    return "".join(traceback[-2:])


@pytest.mark.ipynb
@pytest.mark.parametrize(
    # notebook - ipynb file to execute
    "test_notebook",
    [
        KATIB_INTEGRATION["path"],
        KFP_INTEGRATION["path"],
        MINIO_INTEGRATION["path"],
        MLFLOW_INTEGRATION["path"],
    ],
    ids=[
        KATIB_INTEGRATION["id"],
        KFP_INTEGRATION["id"],
        MINIO_INTEGRATION["id"],
        MLFLOW_INTEGRATION["id"],
    ],
)
def test_integration(test_notebook):
    """Test Integration Generic Wrapper."""
    with open(test_notebook) as nb:
        notebook = nbformat.read(nb, as_version=nbformat.NO_CONVERT)

    ep = ExecutePreprocessor(timeout=-1, kernel_name="python3")
    ep.skip_cells_with_tag = "pytest-skip"

    try:
        log.info(f"Running {test_notebook}...")
        output_notebook, _ = ep.preprocess(notebook, {"metadata": {"path": "./"}})
    except CellExecutionError as e:
        # handle underlying error
        pytest.fail(f"Notebook execution failed with {e.ename}: {e.evalue}")

    for cell in output_notebook.cells:
        metadata = cell.get("metadata", dict)
        if "raises-exception" in metadata.get("tags", []):
            for cell_output in cell.outputs:
                if cell_output.output_type == "error":
                    # extract the error message from the cell output
                    log.error(format_error_message(cell_output.traceback))
                    pytest.fail(cell_output.traceback[-1])
