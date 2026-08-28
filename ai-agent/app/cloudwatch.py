import boto3
from datetime import datetime, timedelta, timezone


AWS_REGION = "us-east-1"


def get_metric(
    cloudwatch,
    instance_id,
    metric_name,
    start_time,
    end_time,
    period=300,
):
    """
    Get an EC2 CloudWatch metric for the specified instance.
    """

    response = cloudwatch.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName=metric_name,
        Dimensions=[
            {
                "Name": "InstanceId",
                "Value": instance_id,
            }
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=period,
        Statistics=["Average"],
    )

    datapoints = sorted(
        response.get("Datapoints", []),
        key=lambda x: x["Timestamp"],
        reverse=True,
    )

    return {
        "label": metric_name,
        "timestamps": [
            dp["Timestamp"].astimezone().isoformat()
            for dp in datapoints
        ],
        "values": [
            dp["Average"]
            for dp in datapoints
        ],
    }


def investigate_cloudwatch(
    instance_id,
    region=AWS_REGION,
    period_hours=1,
):
    """
    Investigate EC2 CloudWatch metrics for a Kubernetes worker node.
    """

    cloudwatch = boto3.client(
        "cloudwatch",
        region_name=region,
    )

    end_time = datetime.now(timezone.utc)

    start_time = (
        end_time
        - timedelta(hours=period_hours)
    )

    metrics = {}

    metric_names = [
        "CPUUtilization",
        "NetworkIn",
        "NetworkOut",
        "StatusCheckFailed",
        "StatusCheckFailed_Instance",
        "StatusCheckFailed_System",
    ]

    for metric_name in metric_names:

        try:

            metrics[
                metric_name.lower()
            ] = get_metric(
                cloudwatch=cloudwatch,
                instance_id=instance_id,
                metric_name=metric_name,
                start_time=start_time,
                end_time=end_time,
            )

        except Exception as error:

            metrics[
                metric_name.lower()
            ] = {
                "label": metric_name,
                "error": str(error),
                "timestamps": [],
                "values": [],
            }

    return {
        "instance_id": instance_id,
        "region": region,
        "period_hours": period_hours,
        "metrics": metrics,
    }


if __name__ == "__main__":

    # Test with your current EKS worker.
    instance_id = "i-00dc40f661508857c"

    print(
        "Investigating CloudWatch metrics..."
    )

    result = investigate_cloudwatch(
        instance_id
    )

    import json

    print(
        json.dumps(
            result,
            indent=2,
            default=str,
        )
    )