# A script to deploy PodSpec charms, these cannot be included in the bundle definition due to https://github.com/canonical/bundle-kubeflow/issues/693
juju deploy ./argo-controller_980dd9f.charm --resource oci-image=172.17.0.2:5000/argoproj/workflow-controller:v3.3.10 --config executor-image=172.17.0.2:5000/argoproj/argoexec:v3.3.8
juju deploy ./argo-server_2618292.charm --resource oci-image=172.17.0.2:5000/argoproj/argocli:v3.3.8
juju deploy ./katib-controller_f371975.charm \
    --resource oci-image=172.17.0.2:5000/kubeflowkatib/katib-controller:v0.16.0-rc.1 \
    --config custom_images='{"default_trial_template": "172.17.0.2:5000/kubeflowkatib/mxnet-mnist:v0.16.0-rc.1", \
        "early_stopping__medianstop": "172.17.0.2:5000/kubeflowkatib/earlystopping-medianstop:v0.16.0-rc.1", \
        "enas_cpu_template": "172.17.0.2:5000/kubeflowkatib/enas-cnn-cifar10-cpu:v0.16.0-rc.1", \
        "metrics_collector_sidecar__stdout": "172.17.0.2:5000/kubeflowkatib/file-metrics-collector:v0.16.0-rc.1", \
        "metrics_collector_sidecar__file": "172.17.0.2:5000/kubeflowkatib/file-metrics-collector:v0.16.0-rc.1", \
        "metrics_collector_sidecar__tensorflow_event": "172.17.0.2:5000/kubeflowkatib/tfevent-metrics-collector:v0.16.0-rc.1", \
        "pytorch_job_template__master": "172.17.0.2:5000/kubeflowkatib/pytorch-mnist-cpu:v0.16.0-rc.1", \
        "pytorch_job_template__worker": "172.17.0.2:5000/kubeflowkatib/pytorch-mnist-cpu:v0.16.0-rc.1", \
        "suggestion__random": "172.17.0.2:5000/kubeflowkatib/suggestion-hyperopt:v0.16.0-rc.1", \
        "suggestion__tpe": "172.17.0.2:5000/kubeflowkatib/suggestion-hyperopt:v0.16.0-rc.1", \
        "suggestion__grid": "172.17.0.2:5000/kubeflowkatib/suggestion-optuna:v0.16.0-rc.1", \
        "suggestion__hyperband": "172.17.0.2:5000/kubeflowkatib/suggestion-hyperband:v0.16.0-rc.1", \
        "suggestion__bayesianoptimization": "172.17.0.2:5000/kubeflowkatib/suggestion-skopt:v0.16.0-rc.1", \
        "suggestion__cmaes": "172.17.0.2:5000/kubeflowkatib/suggestion-goptuna:v0.16.0-rc.1", \
        "suggestion__sobol": "172.17.0.2:5000/kubeflowkatib/suggestion-goptuna:v0.16.0-rc.1", \
        "suggestion__multivariate_tpe": "172.17.0.2:5000/kubeflowkatib/suggestion-optuna:v0.16.0-rc.1", \
        "suggestion__enas": "172.17.0.2:5000/kubeflowkatib/suggestion-enas:v0.16.0-rc.1", \
        "suggestion__darts": "172.17.0.2:5000/kubeflowkatib/suggestion-darts:v0.16.0-rc.1", \
        "suggestion__pbt": "172.17.0.2:5000/kubeflowkatib/suggestion-pbt:v0.16.0-rc.1", }'
juju deploy ./kubeflow-volumes_2ee0a84.charm --resource oci-image=172.17.0.2:5000/kubeflownotebookswg/volumes-web-app:v1.7.0
juju deploy ./minio_3ba39ff.charm --resource oci-image=172.17.0.2:5000/minio/minio:RELEASE.2021-09-03T03-56-13Z

juju relate argo-controller minio
juju relate istio-pilot:ingress kubeflow-volumes:ingress
juju relate kubeflow-dashboard:links kubeflow-volumes:dashboard-links
juju relate kfp-api:object-storage minio:object-storage
juju relate kfp-profile-controller:object-storage minio:object-storage
juju relate kfp-ui:object-storage minio:object-storage