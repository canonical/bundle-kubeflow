# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import os

import nbformat


def format_error_message(traceback: list):
    """Format error message."""
    return "".join(traceback[-2:])


def discover_notebooks(directory):
    """Return a dictionary of notebooks in the provided directory.

    The dictionary contains a mapping between the notebook names (in alphabetical order) and the
    absolute paths to the notebook files. Directories containing IPYNB execution checkpoints are
    ignored.

    Args:
        directory: The directory to search.

    Returns:
        A dictionary of notebook name - notebook file absolute path pairs.
    """
    notebooks = {}
    for root, dirs, files in os.walk(directory):
        # exclude .ipynb_checkpoints directories from the search
        dirs[:] = [d for d in dirs if d != ".ipynb_checkpoints"]
        for file in files:
            if file.endswith(".ipynb"):
                # file name - absolute file path
                notebooks[file.split(".ipynb")[0]] = os.path.abspath(os.path.join(root, file))
    return dict(sorted(notebooks.items()))


def save_notebook(notebook, file_path):
    """Save notebook to a file."""
    with open(file_path, "w", encoding="utf-8") as nb_file:
        nbformat.write(notebook, nb_file)
