Contains unbuilt pipeline samples. To build the samples, install `kfp` from
pypi, then run this command:

    find pipeline-samples/ -name "*.py" -exec bash -c 'dsl-compile --py {} --output charms/pipelines-api/files/$(basename {} .py).yaml' \;

Then, update these files as necessary:

    charms/pipelines-api/files/sample_config.json
    charms/pipelines-api/reactive/pipelines_api.py
