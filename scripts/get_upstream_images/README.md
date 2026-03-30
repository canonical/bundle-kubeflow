# get_upstream_images.py

This script automates the extraction of container image references from the official [Kubeflow Manifests](https://github.com/kubeflow/manifests) repository.

## Usage

From inside this directory:

```shell
python3 get_upstream_images.py <version>
```

The script creates an `images` directory in the folder where you executed the script. Inside, it generates text files containing a sorted, unique list of images, corresponding to the version you specified. You will get one file per processed workgroup, plus an aggregate file containing all images across the entire deployment:
```
images/
├── kf_1.11.0_katib_images.txt
├── kf_1.11.0_kserve_images.txt
├── kf_1.11.0_pipelines_images.txt
└── kf_1.11.0_all_images.txt
```

Using `latest` as the version fetches the manifests corresponding to the `master` branch. To specify a version, use the reference to the corresponding tag:

```shell
python3 extract_images.py v1.11.0
```

You can also skip any working groups by passing the `--skip` argument:

```shell
python3 get_upstream_images.py v1.11.0 --skip spark model-registry
```

The default value of `--skip` is `["spark", "model-registry"]` (since we don't currently have charmed operators for these controllers).
