import os
import json
from datetime import datetime, timedelta, timezone

import boto3
from botocore.exceptions import ClientError


AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

def get_cloudwatch_metrics(
    instance_id,
    region="us-east-1",
    hours=1,
):
    """
    Retrieve recent EC2 CloudWatch metrics.

    Metrics:
    - CPUUtilization
    - NetworkIn
    - NetworkOut
    - StatusCheckFailed
    - StatusCheckFailed_Instance
    - StatusCheckFailed_System
    """

    cloudwatch = boto3.client(
        "cloudwatch",
        region_name=region,
    )

    end_time = datetime.now(
        timezone.utc
    )

    start_time = end_time - timedelta(
        hours=hours
    )

    metrics = [
        (
            "cpu",
            "CPUUtilization",
            "Average",
        ),
        (
            "network_in",
            "NetworkIn",
            "Sum",
        ),
        (
            "network_out",
            "NetworkOut",
            "Sum",
        ),
        (
            "status_check_failed",
            "StatusCheckFailed",
            "Maximum",
        ),
        (
            "status_check_failed_instance",
            "StatusCheckFailed_Instance",
            "Maximum",
        ),
        (
            "status_check_failed_system",
            "StatusCheckFailed_System",
            "Maximum",
        ),
    ]

    queries = []

    for query_id, metric_name, statistic in metrics:

        queries.append(
            {
                "Id": query_id,
                "MetricStat": {
                    "Metric": {
                        "Namespace": "AWS/EC2",
                        "MetricName": metric_name,
                        "Dimensions": [
                            {
                                "Name": "InstanceId",
                                "Value": instance_id,
                            }
                        ],
                    },
                    "Period": 300,
                    "Stat": statistic,
                },
                "ReturnData": True,
            }
        )

    response = cloudwatch.get_metric_data(
        MetricDataQueries=queries,
        StartTime=start_time,
        EndTime=end_time,
        ScanBy="TimestampDescending",
    )

    results = {}

    for result in response.get(
        "MetricDataResults",
        [],
    ):

        results[result["Id"]] = {
            "label": result.get(
                "Label"
            ),
            "timestamps": [
                str(timestamp)
                for timestamp in result.get(
                    "Timestamps",
                    [],
                )
            ],
            "values": result.get(
                "Values",
                [],
            ),
        }

    return {
        "instance_id": instance_id,
        "region": region,
        "period_hours": hours,
        "metrics": results,
    }

def get_ec2_client():
    """Create an EC2 client."""
    return boto3.client(
        "ec2",
        region_name=AWS_REGION,
    )


def find_instance_by_private_dns(private_dns_name):
    """
    Find an EC2 instance using the Kubernetes node private DNS name.
    """

    ec2 = get_ec2_client()

    try:
        response = ec2.describe_instances(
            Filters=[
                {
                    "Name": "private-dns-name",
                    "Values": [private_dns_name],
                }
            ]
        )

        instances = []

        for reservation in response.get("Reservations", []):
            for instance in reservation.get("Instances", []):

                instances.append(
                    {
                        "instance_id": instance.get("InstanceId"),
                        "instance_type": instance.get("InstanceType"),
                        "private_ip": instance.get(
                            "PrivateIpAddress"
                        ),
                        "private_dns": instance.get(
                            "PrivateDnsName"
                        ),
                        "state": instance.get(
                            "State",
                            {}
                        ).get("Name"),
                        "availability_zone": instance.get(
                            "Placement",
                            {}
                        ).get("AvailabilityZone"),
                        "subnet_id": instance.get(
                            "SubnetId"
                        ),
                        "vpc_id": instance.get(
                            "VpcId"
                        ),
                        "launch_time": str(
                            instance.get("LaunchTime")
                        ),
                    }
                )

        return instances

    except ClientError as error:

        return {
            "error": str(error)
        }


def get_instance_status(instance_id):
    """
    Get EC2 system and instance status checks.
    """

    ec2 = get_ec2_client()

    try:
        response = ec2.describe_instance_status(
            InstanceIds=[instance_id],
            IncludeAllInstances=True,
        )

        statuses = []

        for status in response.get(
            "InstanceStatuses",
            []
        ):

            statuses.append(
                {
                    "instance_id": status.get(
                        "InstanceId"
                    ),

                    "instance_state": status.get(
                        "InstanceState",
                        {}
                    ).get("Name"),

                    "system_status": status.get(
                        "SystemStatus",
                        {}
                    ).get("Status"),

                    "instance_status": status.get(
                        "InstanceStatus",
                        {}
                    ).get("Status"),
                }
            )

        return statuses

    except ClientError as error:

        return {
            "error": str(error)
        }


def investigate_node(node_name):
    """
    Perform AWS investigation for a Kubernetes node.
    """

    instances = find_instance_by_private_dns(
        node_name
    )

    if isinstance(instances, dict) and "error" in instances:
        return instances

    if not instances:
        return {
            "node": node_name,
            "status": "NOT_FOUND",
            "message": (
                "No EC2 instance was found "
                "for this Kubernetes node."
            ),
        }

    results = []

    for instance in instances:

        instance_id = instance.get(
            "instance_id"
        )

        status = get_instance_status(
            instance_id
        )

        results.append(
            {
                "node": node_name,
                "ec2": instance,
                "status_checks": status,
            }
        )

    return results


if __name__ == "__main__":

    node = "ip-10-0-12-130.ec2.internal"

    print(
        f"\nInvestigating Kubernetes node: {node}"
    )

    result = investigate_node(node)

    import json

    print(
        json.dumps(
            result,
            indent=2,
            default=str,
        )
    )

    instance_id = "i-00dc40f661508857c"

    print(
        "\nInvestigating CloudWatch metrics..."
    )

    metrics = get_cloudwatch_metrics(
        instance_id
    )

    print(
        json.dumps(
            metrics,
            indent=2,
            default=str,
        )
    )