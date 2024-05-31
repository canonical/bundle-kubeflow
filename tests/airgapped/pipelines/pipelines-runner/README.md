# `charmedkubeflow/pipelines-runner` image

A simple image that contains the `kfp` and `kfp-server-api` packages installed on top of a `python` base image.
The purpose of this image is to use it as the `base-image` for Pipelines components to enable running a Pipeline in an airgapped environment.

## How to publish the image
1. Build the image with the tag, for example for 1.8 we use the tag `ckf-1.8`:
```
docker build -t charmedkubeflow/pipelines-runner:ckf-1.8 .
```
2. Login to docker as `charmedkubeflow` with `docker login`
3. Publish the image to Docker Hub
```
docker push charmedkubeflow/pipelines-runner:ckf-1.8
```