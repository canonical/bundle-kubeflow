# A script to deploy PodSpec charms, these cannot be included in the bundle definition due to https://github.com/canonical/bundle-kubeflow/issues/693
juju deploy ./admission-webhook_a9c1b1d.charm  --resource oci-image=172.17.0.2:5000/kubeflownotebookswg/poddefaults-webhook:v1.7.0
juju deploy ./argo-controller_1b8dd06.charm --resource oci-image=172.17.0.2:5000/argoproj/workflow-controller:v3.3.9 --config executor-image=172.17.0.2:5000/charmedkubeflow/argoexec:v3.3.9_22.04_1
juju deploy ./argo-server_08faf05.charm --resource oci-image=172.17.0.2:5000/argoproj/argocli:v3.3.9
juju deploy ./jupyter-controller_a870440.charm --resource oci-image=172.17.0.2:5000/kubeflownotebookswg/notebook-controller:v1.7.0
juju deploy ./katib-controller_564a127.charm \
    --resource oci-image=172.17.0.2:5000/kubeflowkatib/katib-controller:v0.15.0 \
    --config custom_images='{"default_trial_template": "172.17.0.2:5000/kubeflowkatib/mxnet-mnist:v0.15.0", "early_stopping__medianstop": "172.17.0.2:5000/kubeflowkatib/earlystopping-medianstop:v0.15.0", "enas_cpu_template": "172.17.0.2:5000/kubeflowkatib/enas-cnn-cifar10-cpu:v0.15.0", "metrics_collector_sidecar__stdout": "172.17.0.2:5000/kubeflowkatib/file-metrics-collector:v0.15.0", "metrics_collector_sidecar__file": "172.17.0.2:5000/kubeflowkatib/file-metrics-collector:v0.15.0", "metrics_collector_sidecar__tensorflow_event": "172.17.0.2:5000/kubeflowkatib/tfevent-metrics-collector:v0.15.0", "pytorch_job_template__master": "172.17.0.2:5000/kubeflowkatib/pytorch-mnist-cpu:v0.15.0", "pytorch_job_template__worker": "172.17.0.2:5000/kubeflowkatib/pytorch-mnist-cpu:v0.15.0", "suggestion__random": "172.17.0.2:5000/kubeflowkatib/suggestion-hyperopt:v0.15.0", "suggestion__tpe": "172.17.0.2:5000/kubeflowkatib/suggestion-hyperopt:v0.15.0", "suggestion__grid": "172.17.0.2:5000/kubeflowkatib/suggestion-optuna:v0.15.0", "suggestion__hyperband": "172.17.0.2:5000/kubeflowkatib/suggestion-hyperband:v0.15.0", "suggestion__bayesianoptimization": "172.17.0.2:5000/kubeflowkatib/suggestion-skopt:v0.15.0", "suggestion__cmaes": "172.17.0.2:5000/kubeflowkatib/suggestion-goptuna:v0.15.0", "suggestion__sobol": "172.17.0.2:5000/kubeflowkatib/suggestion-goptuna:v0.15.0", "suggestion__multivariate_tpe": "172.17.0.2:5000/kubeflowkatib/suggestion-optuna:v0.15.0", "suggestion__enas": "172.17.0.2:5000/kubeflowkatib/suggestion-enas:v0.15.0", "suggestion__darts": "172.17.0.2:5000/kubeflowkatib/suggestion-darts:v0.15.0", "suggestion__pbt": "172.17.0.2:5000/kubeflowkatib/suggestion-pbt:v0.15.0", }'
juju deploy ./kfp-persistence_1b2dc2e.charm --resource oci-image=172.17.0.2:5000/charmedkubeflow/persistenceagent:2.0.0-alpha.7_22.04_1
juju deploy ./kfp-profile-controller_a050a69.charm --resource oci-image=172.17.0.2:5000/python:3.7
juju deploy ./kfp-schedwf_15ed6ef.charm --resource oci-image=172.17.0.2:5000/charmedkubeflow/scheduledworkflow:2.0.0-alpha.7_22.04_1
juju deploy ./kfp-ui_f6f6fe4.charm --resource oci-image=172.17.0.2:5000/ml-pipeline/frontend:2.0.0-alpha.7
juju deploy ./kfp-viewer_07fd1d4.charm --resource oci-image=172.17.0.2:5000/charmedkubeflow/viewer-crd-controller:2.0.0-alpha.7_22.04_1
juju deploy ./kfp-viz_755ec1c.charm --resource oci-image=172.17.0.2:5000/charmedkubeflow/visualization-server:2.0.0-alpha.7_20.04_1
juju deploy ./kubeflow-volumes_641d23c.charm --resource oci-image=172.17.0.2:5000/kubeflownotebookswg/volumes-web-app:v1.7.0
juju deploy ./minio_eede92d.charm --resource oci-image=172.17.0.2:5000/minio/minio:RELEASE.2021-09-03T03-56-13Z
juju deploy ./oidc-gatekeeper_29d375d.charm --resource oci-image=172.17.0.2:5000/arrikto/kubeflow/oidc-authservice:e236439
juju deploy ./tensorboard-controller_63d7cbb.charm --resource oci-image=172.17.0.2:5000/kubeflownotebookswg/tensorboard-controller:v1.7.0
juju deploy ./tensorboards-web-app_0faec72.charm --resource oci-image=172.17.0.2:5000/kubeflownotebookswg/tensorboards-web-app:v1.7.0

juju relate argo-controller minio
juju relate dex-auth:oidc-client oidc-gatekeeper:oidc-client
juju relate istio-pilot:ingress kfp-ui:ingress
juju relate istio-pilot:ingress kubeflow-volumes:ingress
juju relate istio-pilot:ingress oidc-gatekeeper:ingress
juju relate istio-pilot:ingress-auth oidc-gatekeeper:ingress-auth
juju relate istio-pilot:ingress tensorboards-web-app:ingress
juju relate istio-pilot:gateway-info tensorboard-controller:gateway-info
juju relate kfp-profile-controller:object-storage minio:object-storage
juju relate kfp-api:object-storage minio:object-storage
juju relate kfp-ui:object-storage minio:object-storage
juju relate kfp-api:kfp-api kfp-persistence:kfp-api
juju relate kfp-api:kfp-api kfp-ui:kfp-api
juju relate kfp-api:kfp-viz kfp-viz:kfp-viz
