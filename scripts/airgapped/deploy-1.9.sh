# This script assumes the presence of `retagged-images.txt` file and `charms` directory in the root dir.
# You can generate these files using the [Airgap utility scripts](https://github.com/canonical/bundle-kubeflow/blob/main/scripts/airgapped/README.md). 

# Define paths and variables
IMAGES="$HOME/retagged-images.txt"
CHARMS_DIR="$HOME/charms"
OCI_REGISTRY=$(head -n 1 $IMAGES | cut -d'/' -f1)

# Function to retrieve the image for a given keyword
img(){
    echo "$(cat $IMAGES | grep $1 | tail -n1)";
    }

# Function to retrieve the charm for a given keyword
charm(){
    echo "$(ls $CHARMS_DIR | grep $1)";
    }

# Ensure correct permissions for the contents of the charms directory so we can `juju deploy` them
sudo chown -R "$USER:" $CHARMS_DIR
cd $CHARMS_DIR

# Deploy the charms by dynamically retrieving the local charm files and images in local registry
# with the help of the `img()` and `charm()` functions defined above.

juju deploy --trust --debug ./$(charm admission-webhook) --resource oci-image=$(img poddefaults-webhook)
juju deploy --trust --debug ./$(charm argo-controller) --resource oci-image=$(img workflow-controller)  --config executor-image=$(img argoexec)
juju deploy --trust --debug ./$(charm dex-auth) --resource oci-image=$(img dex)
juju deploy --trust --debug ./$(charm envoy) --resource oci-image=$(img metadata-envoy)
juju deploy --trust --debug ./$(charm istio-gateway) istio-ingressgateway --config kind=ingress --config proxy-image=$(img istio/proxyv2)

# Get the global tag version for istio from the proxy image tag
proxy_image=$(img istio/proxyv2)
version=${proxy_image##*:}

juju deploy --trust --debug ./$(charm istio-pilot) istio-pilot --config default-gateway=kubeflow-gateway \
    --config image-configuration="pilot-image: 'pilot'
global-tag: '$version'
global-hub: '$OCI_REGISTRY/istio'
global-proxy-image: 'proxyv2'
global-proxy-init-image: 'proxyv2'
grpc-bootstrap-init: 'busybox:1.28'
"

juju deploy --trust --debug ./$(charm jupyter-controller) --resource oci-image=$(img notebook-controller)
juju deploy --trust --debug ./$(charm jupyter-ui) --resource oci-image=$(img jupyter-web-app) \
    --config jupyter-images="['$(img jupyter-scipy)','$(img jupyter-pytorch-full)','$(img jupyter-pytorch-cuda-full)','$(img jupyter-tensorflow-full)','$(img jupyter-tensorflow-cuda-full)']" \
    --config rstudio-images="['$(img rstudio-tidyverse)']" \
    --config vscode-images="['$(img codeserver-python)']"

juju deploy --trust --debug ./$(charm katib-controller)  --resource oci-image=$(img katib-controller) \
     --config custom_images="default_trial_template: '$(img ubuntu:22.04)'
default_trial_template_enas: '$(img enas-cnn-cifar10-cpu)'
default_trial_template_pytorch: '$(img pytorch-mnist-cpu)'
early_stopping__medianstop: '$(img earlystopping-medianstop)'
metrics_collector_sidecar__stdout: '$(img file-metrics-collector)'
metrics_collector_sidecar__file: '$(img file-metrics-collector)'
metrics_collector_sidecar__tensorflow_event: '$(img tfevent-metrics-collector)'
suggestion__random: '$(img suggestion-hyperopt)'
suggestion__tpe: '$(img suggestion-hyperopt)'
suggestion__grid: '$(img suggestion-optuna)'
suggestion__hyperband: '$(img suggestion-hyperband)'
suggestion__bayesianoptimization: '$(img suggestion-skopt)'
suggestion__cmaes: '$(img suggestion-goptuna)'
suggestion__sobol: '$(img suggestion-goptuna)'
suggestion__multivariate_tpe: '$(img suggestion-optuna)'
suggestion__enas: '$(img suggestion-enas)'
suggestion__darts: '$(img suggestion-darts)'
suggestion__pbt: '$(img suggestion-pbt)'
"

juju deploy --trust --debug ./$(charm mysql-k8s) katib-db --constraints="mem=2G" --resource mysql-image=$(img canonical/charmed-mysql)
juju deploy --trust --debug ./$(charm katib-db-manager)  --resource oci-image=$(img katib-db-manager)
juju deploy --trust --debug ./$(charm katib-ui)  --resource oci-image=$(img katib-ui)
juju deploy --trust --debug ./$(charm kfp-api) --resource oci-image=$(img api-server) --config launcher-image=$(img kfp-launcher) --config driver-image=$(img kfp-driver)
juju deploy --trust --debug ./$(charm mysql-k8s) kfp-db --constraints="mem=2G" --resource mysql-image=$(img canonical/charmed-mysql)
juju deploy --trust --debug ./$(charm kfp-metadata-writer) --resource oci-image=$(img metadata-writer)
juju deploy --trust --debug ./$(charm kfp-persistence) --resource oci-image=$(img persistenceagent)
juju deploy --trust --debug ./$(charm kfp-profile-controller) --resource oci-image=$(img python:3.8-20.04) \
    --config custom_images="visualization_server: '$(img visualization-server)'
frontend: '$(img frontend)'
"

juju deploy --trust --debug ./$(charm kfp-schedwf) --resource oci-image=$(img scheduledworkflow)
juju deploy --trust --debug ./$(charm kfp-ui) --resource ml-pipeline-ui=$(img frontend)
juju deploy --trust --debug ./$(charm kfp-viewer) --resource kfp-viewer-image=$(img viewer-crd-controller)
juju deploy --trust --debug ./$(charm kfp-viz) --resource oci-image=$(img visualization-server)
juju deploy --trust --debug ./$(charm knative-eventing) --config namespace=knative-eventing \
     --config custom_images="eventing-controller/eventing-controller: $(img knative-releases/knative.dev/eventing/cmd/controller)
eventing-webhook/eventing-webhook: $(img knative-releases/knative.dev/eventing/cmd/webhook)
imc-dispatcher/dispatcher: $(img knative-releases/knative.dev/eventing/cmd/in_memory/channel_dispatcher)
imc-controller/controller: $(img knative-releases/knative.dev/eventing/cmd/in_memory/channel_controller)
mt-broker-controller/mt-broker-controller: $(img knative-releases/knative.dev/eventing/cmd/mtchannel_broker)
mt-broker-filter/filter: $(img knative-releases/knative.dev/eventing/cmd/broker/filter)
mt-broker-ingress/ingress: $(img knative-releases/knative.dev/eventing/cmd/broker/ingress)
pingsource-mt-adapter/dispatcher: $(img knative-releases/knative.dev/eventing/cmd/mtping)
"
juju deploy --trust --debug ./$(charm knative-operator) --resource knative-operator-image=$(img knative-releases/knative.dev/operator/cmd/operator) --resource knative-operator-webhook-image=$(img knative-releases/knative.dev/operator/cmd/webhook) --config otel-collector-image=$(img otel/opentelemetry-collector)
juju deploy --trust --debug ./$(charm knative-serving) --config namespace=knative-serving --config istio.gateway.namespace=kubeflow --config istio.gateway.name=kubeflow-gateway \
    --config queue_sidecar_image="$(img knative-releases/knative.dev/serving/cmd/queue)" \
    --config custom_images="activator: $(img knative-releases/knative.dev/serving/cmd/activator)
autoscaler: $(img knative-releases/knative.dev/serving/cmd/autoscaler)
controller: $(img knative-releases/knative.dev/serving/cmd/controller)
webhook: $(img knative-releases/knative.dev/serving/cmd/webhook)
autoscaler-hpa: $(img knative-releases/knative.dev/serving/cmd/autoscaler-hpa)
net-istio-controller/controller: $(img knative-releases/knative.dev/net-istio/cmd/controller)
net-istio-webhook/webhook: $(img knative-releases/knative.dev/net-istio/cmd/webhook)
queue-proxy: $(img knative-releases/knative.dev/serving/cmd/queue)
migrate: $(img knative-releases/knative.dev/pkg/apiextensions/storageversion/cmd/migrate)
"

juju deploy --trust --debug ./$(charm kserve-controller) --resource kserve-controller-image=$(img kserve-controller) --resource kube-rbac-proxy-image=$(img kubebuilder/kube-rbac-proxy) --config custom_images="configmap__agent: '$(img charmedkubeflow/kserve-agent)'
configmap__batcher: '$(img charmedkubeflow/kserve-agent)'
configmap__explainers__art: '$(img kserve/art-explainer)'
configmap__logger: '$(img charmedkubeflow/kserve-agent)'
configmap__router: '$(img kserve/router)'
configmap__storageInitializer: '$(img charmedkubeflow/storage-initializer)'
serving_runtimes__huggingfaceserver: '$(img kserve/huggingfaceserver)'
serving_runtimes__lgbserver: '$(img charmedkubeflow/lgbserver)'
serving_runtimes__kserve_mlserver: '$(img seldonio/mlserver)'
serving_runtimes__paddleserver: '$(img charmedkubeflow/paddleserver)'
serving_runtimes__pmmlserver: '$(img charmedkubeflow/pmmlserver)'
serving_runtimes__sklearnserver: '$(img charmedkubeflow/sklearnserver)'
serving_runtimes__tensorflow_serving: '$(img tensorflow/serving)'
serving_runtimes__torchserve: '$(img pytorch/torchserve-kfs)'
serving_runtimes__tritonserver: '$(img nvidia/tritonserver)'
serving_runtimes__xgbserver: '$(img charmedkubeflow/xgbserver)'
"

juju deploy --trust --debug ./$(charm kubeflow-dashboard) --resource oci-image=$(img dashboard)
juju deploy --trust --debug ./$(charm kubeflow-profiles) --resource profile-image=$(img profile-controller) --resource kfam-image=$(img kfam)
juju deploy --trust --debug ./$(charm kubeflow-roles)
juju deploy --trust --debug ./$(charm kubeflow-volumes) --resource oci-image=$(img volumes-web-app)
juju deploy --trust --debug ./$(charm metacontroller-operator) --config metacontroller-image=$(img metacontroller)
juju deploy --trust --debug ./$(charm mlmd) --resource oci-image=$(img ml_metadata_store_server)

juju deploy --debug ./$(charm minio) --resource oci-image=$(img minio)
juju deploy --trust --debug ./$(charm oidc-gatekeeper) --resource oci-image=$(img oidc-authservice)
juju deploy --trust --debug ./$(charm pvcviewer-operator) --series=focal --resource oci-image=$(img pvcviewer-controller)

juju deploy --trust --debug ./$(charm tensorboard-controller) --resource tensorboard-controller-image=$(img tensorboard-controller)
juju deploy --trust --debug ./$(charm tensorboards-web-app) --resource tensorboards-web-app-image=$(img tensorboards-web-app)
juju deploy --trust --debug ./$(charm training-operator) --config training-operator-image=$(img training-operator)

# Add the relations from the 1.9 bundle
juju relate argo-controller minio
juju relate dex-auth:dex-oidc-config oidc-gatekeeper:dex-oidc-config
juju relate dex-auth:oidc-client oidc-gatekeeper:oidc-client
juju relate istio-pilot:ingress dex-auth:ingress
juju relate istio-pilot:ingress envoy:ingress
juju relate istio-pilot:ingress jupyter-ui:ingress
juju relate istio-pilot:ingress katib-ui:ingress
juju relate istio-pilot:ingress kfp-ui:ingress
juju relate istio-pilot:ingress kubeflow-dashboard:ingress
juju relate istio-pilot:ingress kubeflow-volumes:ingress
juju relate istio-pilot:ingress oidc-gatekeeper:ingress
juju relate istio-pilot:ingress-auth oidc-gatekeeper:ingress-auth
juju relate istio-pilot:istio-pilot istio-ingressgateway:istio-pilot
juju relate istio-pilot:ingress tensorboards-web-app:ingress
juju relate istio-pilot:gateway-info tensorboard-controller:gateway-info
juju relate katib-db-manager:k8s-service-info katib-controller:k8s-service-info
juju relate katib-db-manager:relational-db katib-db:database
juju relate kfp-api:relational-db kfp-db:database
juju relate kfp-api:kfp-api kfp-persistence:kfp-api
juju relate kfp-api:kfp-api kfp-ui:kfp-api
juju relate kfp-api:kfp-viz kfp-viz:kfp-viz
juju relate kfp-api:object-storage minio:object-storage
juju relate kfp-profile-controller:object-storage minio:object-storage
juju relate kfp-ui:object-storage minio:object-storage
juju relate kserve-controller:ingress-gateway istio-pilot:gateway-info
juju relate kserve-controller:local-gateway knative-serving:local-gateway
juju relate kubeflow-profiles kubeflow-dashboard
juju relate kubeflow-dashboard:links jupyter-ui:dashboard-links
juju relate kubeflow-dashboard:links katib-ui:dashboard-links
juju relate kubeflow-dashboard:links kfp-ui:dashboard-links
juju relate kubeflow-dashboard:links kubeflow-volumes:dashboard-links
juju relate kubeflow-dashboard:links tensorboards-web-app:dashboard-links
juju relate kubeflow-dashboard:links training-operator:dashboard-links
juju relate mlmd:grpc envoy:grpc
juju relate mlmd:grpc kfp-metadata-writer:grpc
