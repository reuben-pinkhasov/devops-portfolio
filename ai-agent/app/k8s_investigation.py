from kubernetes import client
from kubernetes.client.rest import ApiException


def safe_value(value):
    """
    Convert Kubernetes objects into JSON-friendly values.
    """
    if value is None:
        return None

    return str(value)


def investigate_node(node_name):
    """
    Deep investigation of a Kubernetes node.
    """

    v1 = client.CoreV1Api()

    result = {
        "node": node_name,
        "conditions": [],
        "capacity": {},
        "allocatable": {},
        "info": {},
        "taints": [],
        "events": [],
    }

    try:
        node = v1.read_node(node_name)

        # =====================================================
        # NODE CONDITIONS
        # =====================================================

        for condition in node.status.conditions or []:

            result["conditions"].append(
                {
                    "type": condition.type,
                    "status": condition.status,
                    "reason": safe_value(
                        condition.reason
                    ),
                    "message": safe_value(
                        condition.message
                    ),
                    "last_heartbeat_time":
                        safe_value(
                            condition.last_heartbeat_time
                        ),
                    "last_transition_time":
                        safe_value(
                            condition.last_transition_time
                        ),
                }
            )

        # =====================================================
        # CAPACITY
        # =====================================================

        if node.status.capacity:

            result["capacity"] = {
                key: safe_value(value)
                for key, value
                in node.status.capacity.items()
            }

        # =====================================================
        # ALLOCATABLE
        # =====================================================

        if node.status.allocatable:

            result["allocatable"] = {
                key: safe_value(value)
                for key, value
                in node.status.allocatable.items()
            }

        # =====================================================
        # NODE INFO
        # =====================================================

        if node.status.node_info:

            info = node.status.node_info

            result["info"] = {
                "architecture":
                    info.architecture,

                "operating_system":
                    info.operating_system,

                "os_image":
                    info.os_image,

                "kernel_version":
                    info.kernel_version,

                "container_runtime_version":
                    info.container_runtime_version,

                "kubelet_version":
                    info.kubelet_version,

                "kube_proxy_version":
                    info.kube_proxy_version,
            }

        # =====================================================
        # TAINTS
        # =====================================================

        for taint in node.spec.taints or []:

            result["taints"].append(
                {
                    "key": taint.key,
                    "value": safe_value(
                        taint.value
                    ),
                    "effect": taint.effect,
                }
            )

        # =====================================================
        # NODE EVENTS
        # =====================================================

        try:

            events = v1.list_event_for_all_namespaces(
                field_selector=f"involvedObject.kind=Node,"
                               f"involvedObject.name={node_name}"
            )

            for event in events.items:

                result["events"].append(
                    {
                        "reason":
                            event.reason,

                        "type":
                            event.type,

                        "message":
                            event.message,

                        "count":
                            event.count,

                        "first_timestamp":
                            safe_value(
                                event.first_timestamp
                            ),

                        "last_timestamp":
                            safe_value(
                                event.last_timestamp
                            ),
                    }
                )

        except ApiException:
            pass

    except ApiException as error:

        result["error"] = str(error)

    return result


def investigate_pod(
    pod_name,
    namespace,
):
    """
    Deep investigation of a Kubernetes pod.
    """

    v1 = client.CoreV1Api()

    result = {
        "pod": pod_name,
        "namespace": namespace,
        "phase": None,
        "conditions": [],
        "container_statuses": [],
        "init_container_statuses": [],
        "events": [],
        "logs": {},
    }

    try:

        pod = v1.read_namespaced_pod(
            pod_name,
            namespace,
        )

        # =====================================================
        # POD PHASE
        # =====================================================

        if pod.status:

            result["phase"] = safe_value(
                pod.status.phase
            )

        # =====================================================
        # POD CONDITIONS
        # =====================================================

        for condition in pod.status.conditions or []:

            result["conditions"].append(
                {
                    "type":
                        condition.type,

                    "status":
                        condition.status,

                    "reason":
                        safe_value(
                            condition.reason
                        ),

                    "message":
                        safe_value(
                            condition.message
                        ),
                }
            )

        # =====================================================
        # CONTAINER STATUSES
        # =====================================================

        for status in (
            pod.status.container_statuses
            or []
        ):

            container = {
                "name":
                    status.name,

                "ready":
                    status.ready,

                "restart_count":
                    status.restart_count,

                "state": {},
            }

            if status.state:

                if status.state.running:

                    container["state"] = {
                        "type": "Running",
                        "started_at":
                            safe_value(
                                status.state.running.started_at
                            ),
                    }

                elif status.state.waiting:

                    container["state"] = {
                        "type": "Waiting",
                        "reason":
                            status.state.waiting.reason,
                        "message":
                            status.state.waiting.message,
                    }

                elif status.state.terminated:

                    container["state"] = {
                        "type": "Terminated",
                        "reason":
                            status.state.terminated.reason,
                        "exit_code":
                            status.state.terminated.exit_code,
                        "message":
                            status.state.terminated.message,
                    }

            result[
                "container_statuses"
            ].append(container)

        # =====================================================
        # INIT CONTAINERS
        # =====================================================

        for status in (
            pod.status.init_container_statuses
            or []
        ):

            result[
                "init_container_statuses"
            ].append(
                {
                    "name":
                        status.name,

                    "ready":
                        status.ready,

                    "restart_count":
                        status.restart_count,
                }
            )

        # =====================================================
        # POD EVENTS
        # =====================================================

        try:

            events = v1.list_namespaced_event(
                namespace,
                field_selector=(
                    f"involvedObject.kind=Pod,"
                    f"involvedObject.name={pod_name}"
                ),
            )

            for event in events.items:

                result["events"].append(
                    {
                        "reason":
                            event.reason,

                        "type":
                            event.type,

                        "message":
                            event.message,

                        "count":
                            event.count,

                        "last_timestamp":
                            safe_value(
                                event.last_timestamp
                            ),
                    }
                )

        except ApiException:
            pass

        # =====================================================
        # POD LOGS
        # =====================================================

        for container in (
            pod.spec.containers or []
        ):

            container_name = container.name

            try:

                logs = v1.read_namespaced_pod_log(
                    name=pod_name,
                    namespace=namespace,
                    container=container_name,
                    tail_lines=100,
                )

                result["logs"][
                    container_name
                ] = logs

            except ApiException as error:

                result["logs"][
                    container_name
                ] = (
                    f"Unable to retrieve logs: "
                    f"{error}"
                )

    except ApiException as error:

        result["error"] = str(error)

    return result