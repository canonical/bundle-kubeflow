from lightkube.resources.core_v1 import Service


def get_ingress_url(lightkube_client, model_name):
    gateway_svc = lightkube_client.get(
        Service, "istio-ingressgateway-workload", namespace=model_name
    )

    public_url = f"http://{gateway_svc.status.loadBalancer.ingress[0].ip}.nip.io"
    return public_url
