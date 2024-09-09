# Testing Pipelines in Airgapped

## The `kfp-airgapped-ipynb` Notebook
To test Pipelines in Airgapped, we are using the Notebook in this directory. It contains the Data passing pipeline example, with the configuration of the Pipeline components to use the `pipelines-runner` [image](./pipelines-runner/README.md).

The `pipelines-runner` image will be included in your airgapped environment given that you used the [Airgapped test scripts](../../README.md). It's specifically added in the [`get-all-images.py` script](../../../../scripts/airgapped/get-all-images.py).

## How to test Pipelines in an Airgapped environment
1. Prepare the airgapped environment and Deploy CKF by following the steps in [Airgapped test scripts](../../README.md).
2. Connect to the dashboard by visiting the IP of your airgapped VM. To get the IP run:
```
lxc ls | grep eth0
```
3. Go to the `Notebooks` tab, create a new Notebook server and choose `jupyter-tensorflow-full` image from the dropdown.
4. Connect to the Notebook server and upload the `kfp-airgapped-ipynb` Notebook.
5. Run the Notebook.
6. Click on `Run details` from the output of the last cell in the Notebook to see the status of the Pipeline run.
