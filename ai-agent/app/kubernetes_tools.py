from kubernetes import client, config


def load_kubernetes_config():
    """
    Load Kubernetes configuration from the local kubeconfig.
    """

    config.load_kube_config()

def get_nodes():
    """
    Get Kubernetes node information including taints.
    """

    load_kubernetes_config()

    v1 = client.CoreV1Api()

    nodes = v1.list_node()

    result = []

    for node in nodes.items:
        taints = []

        for taint in node.spec.taints or []:
            taints.append(
                {
                    "key": taint.key,
                    "value": taint.value,
                    "effect": taint.effect,
                }
            )

        conditions = {}

        for condition in node.status.conditions or []:
            conditions[condition.type] = condition.status

        result.append(
            {
                "name": node.metadata.name,
                "ready": conditions.get("Ready"),
                "taints": taints,
                "architecture": node.status.node_info.architecture,
                "os": node.status.node_info.operating_system,
                "kubelet_version": node.status.node_info.kubelet_version,
            }
        )

    return result

def get_pods(namespace: str = "default"):
    """
    Get basic information about pods in a namespace.
    """

    load_kubernetes_config()

    v1 = client.CoreV1Api()
    pods = v1.list_namespaced_pod(namespace=namespace)

    result = []

    for pod in pods.items:
        container_statuses = pod.status.container_statuses or []

        restart_count = sum(
            status.restart_count
            for status in container_statuses
        )

        ready_count = sum(
            1
            for status in container_statuses
            if status.ready
        )

        total_containers = len(container_statuses)

        result.append(
            {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "phase": pod.status.phase,
                "node": pod.spec.node_name,
                "ready": f"{ready_count}/{total_containers}",
                "restarts": restart_count,
            }
        )
    return result

def get_deployments(namespace: str = "default"):
    """
    Get deployment status information.
    """

    load_kubernetes_config()

    apps_v1 = client.AppsV1Api()
    deployments = apps_v1.list_namespaced_deployment(
        namespace=namespace
    )

    result = []

    for deployment in deployments.items:
        result.append(
            {
                "name": deployment.metadata.name,
                "namespace": deployment.metadata.namespace,
                "desired_replicas": deployment.spec.replicas,
                "ready_replicas": deployment.status.ready_replicas or 0,
                "available_replicas": (
                    deployment.status.available_replicas or 0
                ),
                "updated_replicas": (
                    deployment.status.updated_replicas or 0
                ),
            }
        )

    return result

def get_services(namespace: str = "default"):
    """
    Get Kubernetes Services.
    """

    load_kubernetes_config()

    v1 = client.CoreV1Api()
    services = v1.list_namespaced_service(namespace=namespace)

    result = []

    for service in services.items:
        ports = []

        for port in service.spec.ports or []:
            ports.append(
                {
                    "port": port.port,
                    "target_port": str(port.target_port),
                    "protocol": port.protocol,
                }
            )

        result.append(
            {
                "name": service.metadata.name,
                "namespace": service.metadata.namespace,
                "type": service.spec.type,
                "cluster_ip": service.spec.cluster_ip,
                "selector": service.spec.selector or {},
                "ports": ports,
            }
        )
        
    return result

def get_events(namespace: str = None):
    """
    Get Kubernetes events.

    If namespace is None, return events from all namespaces.
    """

    load_kubernetes_config()

    v1 = client.CoreV1Api()

    if namespace:
        events = v1.list_namespaced_event(
            namespace=namespace
        )
    else:
        events = v1.list_event_for_all_namespaces()

    result = []

    for event in events.items:
        result.append(
            {
                "namespace": event.metadata.namespace,
                "reason": event.reason,
                "type": event.type,
                "message": event.message,
                "object": (
                    f"{event.involved_object.kind}/"
                    f"{event.involved_object.name}"
                ),
                "count": event.count,
            }
        )

    return result

def get_pod_logs(
    pod_name: str,
    namespace: str = "default",
    tail_lines: int = 100,
):
    """
    Get recent logs from a pod.
    """

    load_kubernetes_config()

    v1 = client.CoreV1Api()

    logs = v1.read_namespaced_pod_log(
        name=pod_name,
        namespace=namespace,
        tail_lines=tail_lines,
    )

    return logs

def get_hpa(namespace: str = "default"):
    """
    Get Horizontal Pod Autoscaler information.
    """

    load_kubernetes_config()

    autoscaling_v2 = client.AutoscalingV2Api()

    hpas = autoscaling_v2.list_namespaced_horizontal_pod_autoscaler(
        namespace=namespace
    )

    result = []

    for hpa in hpas.items:
        result.append(
            {
                "name": hpa.metadata.name,
                "namespace": hpa.metadata.namespace,
                "min_replicas": hpa.spec.min_replicas,
                "max_replicas": hpa.spec.max_replicas,
                "current_replicas": hpa.status.current_replicas or 0,
                "desired_replicas": hpa.status.desired_replicas or 0,
            }
        )

    return result
  
      