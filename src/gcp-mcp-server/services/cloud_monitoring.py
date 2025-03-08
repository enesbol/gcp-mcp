import datetime
import json
from typing import Dict, List, Optional

from google.cloud import monitoring_v3
from google.protobuf.duration_pb2 import Duration
from google.protobuf.timestamp_pb2 import Timestamp
from services import client_instances


def register(mcp_instance):
    """Register all Cloud Monitoring resources and tools with the MCP instance."""

    # Resources
    @mcp_instance.resource("gcp://monitoring/{project_id}/metrics")
    def list_metrics_resource(project_id: str = None) -> str:
        """List all available metrics for a GCP project"""
        try:
            # Get client from client_instances
            client = client_instances.get_clients().monitoring
            project_id = project_id or client_instances.get_project_id()

            name = f"projects/{project_id}"
            metrics = client.list_metric_descriptors(name=name)

            result = []
            for metric in metrics:
                result.append(
                    {
                        "name": metric.name,
                        "type": metric.type,
                        "display_name": metric.display_name,
                        "description": metric.description,
                        "kind": monitoring_v3.MetricDescriptor.MetricKind.Name(
                            metric.metric_kind
                        ),
                        "value_type": monitoring_v3.MetricDescriptor.ValueType.Name(
                            metric.value_type
                        ),
                        "unit": metric.unit,
                    }
                )

            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    @mcp_instance.resource("gcp://monitoring/{project_id}/alerts")
    def list_alerts_resource(project_id: str = None) -> str:
        """List all alert policies for a GCP project"""
        try:
            # Get client from client_instances
            client = client_instances.get_clients().monitoring
            project_id = project_id or client_instances.get_project_id()

            name = f"projects/{project_id}"
            policies = client.list_alert_policies(name=name)

            result = []
            for policy in policies:
                result.append(
                    {
                        "name": policy.name,
                        "display_name": policy.display_name,
                        "enabled": policy.enabled,
                        "conditions_count": len(policy.conditions),
                        "creation_time": policy.creation_record.mutate_time.ToDatetime().isoformat()
                        if policy.creation_record and policy.creation_record.mutate_time
                        else None,
                        "notification_channels": [
                            chan.split("/")[-1] for chan in policy.notification_channels
                        ]
                        if policy.notification_channels
                        else [],
                    }
                )

            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    @mcp_instance.resource("gcp://monitoring/{project_id}/alert/{alert_id}")
    def get_alert_resource(project_id: str = None, alert_id: str = None) -> str:
        """Get details for a specific alert policy"""
        try:
            # Get client from client_instances
            client = client_instances.get_clients().monitoring
            project_id = project_id or client_instances.get_project_id()

            name = f"projects/{project_id}/alertPolicies/{alert_id}"
            policy = client.get_alert_policy(name=name)

            conditions = []
            for condition in policy.conditions:
                condition_data = {
                    "name": condition.name,
                    "display_name": condition.display_name,
                    "type": condition.condition_type_name
                    if hasattr(condition, "condition_type_name")
                    else None,
                }

                # Add condition-specific details
                if condition.HasField("condition_threshold"):
                    threshold = condition.condition_threshold
                    condition_data["threshold"] = {
                        "filter": threshold.filter,
                        "comparison": monitoring_v3.ComparisonType.Name(
                            threshold.comparison
                        )
                        if threshold.comparison
                        else None,
                        "threshold_value": threshold.threshold_value,
                        "duration": f"{threshold.duration.seconds}s"
                        if threshold.duration
                        else None,
                        "aggregation": {
                            "alignment_period": f"{threshold.aggregations[0].alignment_period.seconds}s"
                            if threshold.aggregations
                            and threshold.aggregations[0].alignment_period
                            else None,
                            "per_series_aligner": monitoring_v3.Aggregation.Aligner.Name(
                                threshold.aggregations[0].per_series_aligner
                            )
                            if threshold.aggregations
                            and threshold.aggregations[0].per_series_aligner
                            else None,
                            "cross_series_reducer": monitoring_v3.Aggregation.Reducer.Name(
                                threshold.aggregations[0].cross_series_reducer
                            )
                            if threshold.aggregations
                            and threshold.aggregations[0].cross_series_reducer
                            else None,
                        }
                        if threshold.aggregations and len(threshold.aggregations) > 0
                        else None,
                    }

                conditions.append(condition_data)

            result = {
                "name": policy.name,
                "display_name": policy.display_name,
                "enabled": policy.enabled,
                "conditions": conditions,
                "combiner": monitoring_v3.AlertPolicy.ConditionCombinerType.Name(
                    policy.combiner
                )
                if policy.combiner
                else None,
                "notification_channels": policy.notification_channels,
                "creation_time": policy.creation_record.mutate_time.ToDatetime().isoformat()
                if policy.creation_record and policy.creation_record.mutate_time
                else None,
                "documentation": {
                    "content": policy.documentation.content,
                    "mime_type": policy.documentation.mime_type,
                }
                if policy.HasField("documentation")
                else None,
            }

            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    @mcp_instance.resource("gcp://monitoring/{project_id}/notification_channels")
    def list_notification_channels_resource(project_id: str = None) -> str:
        """List notification channels for a GCP project"""
        try:
            # Get client from client_instances
            client = client_instances.get_clients().monitoring
            project_id = project_id or client_instances.get_project_id()

            name = f"projects/{project_id}"
            channels = client.list_notification_channels(name=name)

            result = []
            for channel in channels:
                result.append(
                    {
                        "name": channel.name,
                        "type": channel.type,
                        "display_name": channel.display_name,
                        "description": channel.description,
                        "verification_status": monitoring_v3.NotificationChannel.VerificationStatus.Name(
                            channel.verification_status
                        )
                        if channel.verification_status
                        else None,
                        "enabled": channel.enabled,
                        "labels": dict(channel.labels) if channel.labels else {},
                    }
                )

            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    # Tools
    @mcp_instance.tool()
    def list_metrics(project_id: str = None, filter_str: str = "") -> str:
        """
        List metrics in a GCP project with optional filtering

        Args:
            project_id: GCP project ID (defaults to configured project)
            filter_str: Optional filter string to narrow results (e.g., "metric.type = starts_with(\"compute.googleapis.com\")")
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().monitoring
            project_id = project_id or client_instances.get_project_id()

            parent = f"projects/{project_id}"
            request = monitoring_v3.ListMetricDescriptorsRequest(
                name=parent, filter=filter_str
            )

            print(f"Listing metrics for project {project_id}...")
            metrics = client.list_metric_descriptors(request=request)

            result = []
            for metric in metrics:
                result.append(
                    {
                        "name": metric.name,
                        "type": metric.type,
                        "display_name": metric.display_name,
                        "description": metric.description,
                        "kind": monitoring_v3.MetricDescriptor.MetricKind.Name(
                            metric.metric_kind
                        ),
                        "value_type": monitoring_v3.MetricDescriptor.ValueType.Name(
                            metric.value_type
                        ),
                        "unit": metric.unit,
                    }
                )

            return json.dumps(
                {"status": "success", "metrics": result, "count": len(result)}, indent=2
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def fetch_metric_timeseries(
        metric_type: str,
        project_id: str = None,
        filter_additions: str = "",
        hours: int = 1,
        alignment_period_seconds: int = 60,
    ) -> str:
        """
        Fetch time series data for a specific metric

        Args:
            metric_type: The metric type (e.g., "compute.googleapis.com/instance/cpu/utilization")
            project_id: GCP project ID (defaults to configured project)
            filter_additions: Additional filter criteria (e.g., "resource.labels.instance_id = \"my-instance\"")
            hours: Number of hours of data to fetch (default: 1)
            alignment_period_seconds: Data point alignment period in seconds (default: 60)
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().monitoring
            project_id = project_id or client_instances.get_project_id()

            # Build the filter
            filter_str = f'metric.type = "{metric_type}"'
            if filter_additions:
                filter_str += f" AND {filter_additions}"

            # Calculate time interval
            now = datetime.datetime.utcnow()
            seconds = int(now.timestamp())
            end_time = Timestamp(seconds=seconds)

            start_time = Timestamp(seconds=seconds - hours * 3600)

            # Create interval
            interval = monitoring_v3.TimeInterval(
                end_time=end_time, start_time=start_time
            )

            # Create aggregation
            aggregation = monitoring_v3.Aggregation(
                alignment_period=Duration(seconds=alignment_period_seconds),
                per_series_aligner=monitoring_v3.Aggregation.Aligner.ALIGN_MEAN,
            )

            # Build request
            request = monitoring_v3.ListTimeSeriesRequest(
                name=f"projects/{project_id}",
                filter=filter_str,
                interval=interval,
                view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
                aggregation=aggregation,
            )

            print(f"Fetching time series data for {metric_type}...")
            time_series = client.list_time_series(request=request)

            result = []
            for series in time_series:
                data_points = []
                for point in series.points:
                    point_time = point.interval.end_time.ToDatetime().isoformat()

                    # Handle different value types
                    if point.value.HasField("double_value"):
                        value = point.value.double_value
                    elif point.value.HasField("int64_value"):
                        value = point.value.int64_value
                    elif point.value.HasField("bool_value"):
                        value = point.value.bool_value
                    elif point.value.HasField("string_value"):
                        value = point.value.string_value
                    elif point.value.HasField("distribution_value"):
                        value = (
                            "distribution"  # Simplified, as distributions are complex
                        )
                    else:
                        value = None

                    data_points.append({"time": point_time, "value": value})

                series_data = {
                    "metric": dict(series.metric.labels)
                    if series.metric and series.metric.labels
                    else {},
                    "resource": {
                        "type": series.resource.type,
                        "labels": dict(series.resource.labels)
                        if series.resource and series.resource.labels
                        else {},
                    }
                    if series.resource
                    else {},
                    "points": data_points,
                }
                result.append(series_data)

            return json.dumps(
                {
                    "status": "success",
                    "metric_type": metric_type,
                    "time_range": {
                        "start": start_time.ToDatetime().isoformat(),
                        "end": end_time.ToDatetime().isoformat(),
                    },
                    "time_series": result,
                    "count": len(result),
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def list_alert_policies(project_id: str = None, filter_str: str = "") -> str:
        """
        List alert policies in a GCP project with optional filtering

        Args:
            project_id: GCP project ID (defaults to configured project)
            filter_str: Optional filter string (e.g., "display_name = \"High CPU Alert\"")
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().monitoring
            project_id = project_id or client_instances.get_project_id()

            parent = f"projects/{project_id}"
            request = monitoring_v3.ListAlertPoliciesRequest(
                name=parent, filter=filter_str
            )

            print(f"Listing alert policies for project {project_id}...")
            policies = client.list_alert_policies(request=request)

            result = []
            for policy in policies:
                policy_data = {
                    "name": policy.name,
                    "display_name": policy.display_name,
                    "enabled": policy.enabled,
                    "conditions_count": len(policy.conditions),
                    "combiner": monitoring_v3.AlertPolicy.ConditionCombinerType.Name(
                        policy.combiner
                    )
                    if policy.combiner
                    else None,
                    "notification_channels": [
                        chan.split("/")[-1] for chan in policy.notification_channels
                    ]
                    if policy.notification_channels
                    else [],
                    "creation_time": policy.creation_record.mutate_time.ToDatetime().isoformat()
                    if policy.creation_record and policy.creation_record.mutate_time
                    else None,
                }
                result.append(policy_data)

            return json.dumps(
                {"status": "success", "alert_policies": result, "count": len(result)},
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def create_metric_threshold_alert(
        display_name: str,
        metric_type: str,
        filter_str: str,
        threshold_value: float,
        project_id: str = None,
        comparison: str = "COMPARISON_GT",
        duration_seconds: int = 300,
        alignment_period_seconds: int = 60,
        aligner: str = "ALIGN_MEAN",
        reducer: str = "REDUCE_MEAN",
        notification_channels: Optional[List[str]] = None,
        documentation: str = "",
        enabled: bool = True,
    ) -> str:
        """
        Create a metric threshold alert policy

        Args:
            display_name: Human-readable name for the alert
            metric_type: The metric to alert on (e.g., "compute.googleapis.com/instance/cpu/utilization")
            filter_str: Filter string to define which resources to monitor
            threshold_value: The threshold value to trigger the alert
            project_id: GCP project ID (defaults to configured project)
            comparison: Comparison type (COMPARISON_GT, COMPARISON_GE, COMPARISON_LT, COMPARISON_LE, COMPARISON_EQ, COMPARISON_NE)
            duration_seconds: Duration in seconds the condition must be met to trigger
            alignment_period_seconds: Period in seconds for data point alignment
            aligner: Per-series aligner (ALIGN_MEAN, ALIGN_MAX, ALIGN_MIN, etc.)
            reducer: Cross-series reducer (REDUCE_MEAN, REDUCE_MAX, REDUCE_MIN, etc.)
            notification_channels: List of notification channel IDs
            documentation: Documentation for the alert (markdown supported)
            enabled: Whether the alert should be enabled
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().monitoring
            project_id = project_id or client_instances.get_project_id()

            # Validate and convert enums
            try:
                comparison_enum = getattr(monitoring_v3.ComparisonType, comparison)
                aligner_enum = getattr(monitoring_v3.Aggregation.Aligner, aligner)
                reducer_enum = getattr(monitoring_v3.Aggregation.Reducer, reducer)
            except AttributeError as e:
                return json.dumps(
                    {
                        "status": "error",
                        "message": f"Invalid enum value: {str(e)}. Please check documentation for valid values.",
                    },
                    indent=2,
                )

            # Prepare notification channels with full paths
            full_notification_channels = []
            if notification_channels:
                for channel in notification_channels:
                    if not channel.startswith(
                        f"projects/{project_id}/notificationChannels/"
                    ):
                        channel = (
                            f"projects/{project_id}/notificationChannels/{channel}"
                        )
                    full_notification_channels.append(channel)

            # Create aggregation
            aggregation = monitoring_v3.Aggregation(
                alignment_period=Duration(seconds=alignment_period_seconds),
                per_series_aligner=aligner_enum,
                cross_series_reducer=reducer_enum,
                group_by_fields=[],
            )

            # Create condition threshold
            condition_threshold = monitoring_v3.AlertPolicy.Condition.MetricThreshold(
                filter=f'metric.type = "{metric_type}" AND {filter_str}',
                comparison=comparison_enum,
                threshold_value=threshold_value,
                duration=Duration(seconds=duration_seconds),
                aggregations=[aggregation],
            )

            # Create condition
            condition = monitoring_v3.AlertPolicy.Condition(
                display_name=f"Threshold condition for {display_name}",
                condition_threshold=condition_threshold,
            )

            # Create alert policy
            alert_policy = monitoring_v3.AlertPolicy(
                display_name=display_name,
                conditions=[condition],
                combiner=monitoring_v3.AlertPolicy.ConditionCombinerType.OR,
                notification_channels=full_notification_channels,
                enabled=monitoring_v3.BoolValue(value=enabled),
            )

            # Add documentation if provided
            if documentation:
                alert_policy.documentation = monitoring_v3.AlertPolicy.Documentation(
                    content=documentation, mime_type="text/markdown"
                )

            # Create the request
            request = monitoring_v3.CreateAlertPolicyRequest(
                name=f"projects/{project_id}", alert_policy=alert_policy
            )

            print(f"Creating alert policy: {display_name}...")
            response = client.create_alert_policy(request=request)

            return json.dumps(
                {
                    "status": "success",
                    "name": response.name,
                    "display_name": response.display_name,
                    "enabled": response.enabled,
                    "conditions_count": len(response.conditions),
                    "notification_channels": response.notification_channels,
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def update_alert_policy(
        alert_id: str,
        project_id: str = None,
        display_name: Optional[str] = None,
        notification_channels: Optional[List[str]] = None,
        enabled: Optional[bool] = None,
        documentation: Optional[str] = None,
    ) -> str:
        """
        Update an existing alert policy

        Args:
            alert_id: ID of the alert to update
            project_id: GCP project ID (defaults to configured project)
            display_name: New name for the alert
            notification_channels: List of notification channel IDs
            enabled: Whether the alert should be enabled
            documentation: Documentation for the alert (markdown supported)
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().monitoring
            project_id = project_id or client_instances.get_project_id()

            # Get the existing policy
            name = f"projects/{project_id}/alertPolicies/{alert_id}"
            policy = client.get_alert_policy(name=name)

            # Update fields if provided
            if display_name:
                policy.display_name = display_name

            if notification_channels is not None:
                full_notification_channels = []
                for channel in notification_channels:
                    if not channel.startswith(
                        f"projects/{project_id}/notificationChannels/"
                    ):
                        channel = (
                            f"projects/{project_id}/notificationChannels/{channel}"
                        )
                    full_notification_channels.append(channel)
                policy.notification_channels = full_notification_channels

            if enabled is not None:
                policy.enabled = monitoring_v3.BoolValue(value=enabled)

            if documentation is not None:
                policy.documentation = monitoring_v3.AlertPolicy.Documentation(
                    content=documentation, mime_type="text/markdown"
                )

            # Create update mask
            update_mask = []
            if display_name:
                update_mask.append("display_name")
            if notification_channels is not None:
                update_mask.append("notification_channels")
            if enabled is not None:
                update_mask.append("enabled")
            if documentation is not None:
                update_mask.append("documentation")

            # Update the policy
            request = monitoring_v3.UpdateAlertPolicyRequest(
                alert_policy=policy, update_mask={"paths": update_mask}
            )

            print(f"Updating alert policy: {policy.name}...")
            response = client.update_alert_policy(request=request)

            return json.dumps(
                {
                    "status": "success",
                    "name": response.name,
                    "display_name": response.display_name,
                    "enabled": response.enabled,
                    "conditions_count": len(response.conditions),
                    "notification_channels": [
                        chan.split("/")[-1] for chan in response.notification_channels
                    ]
                    if response.notification_channels
                    else [],
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def delete_alert_policy(alert_id: str, project_id: str = None) -> str:
        """
        Delete an alert policy

        Args:
            alert_id: ID of the alert to delete
            project_id: GCP project ID (defaults to configured project)
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().monitoring
            project_id = project_id or client_instances.get_project_id()

            name = f"projects/{project_id}/alertPolicies/{alert_id}"

            print(f"Deleting alert policy: {alert_id}...")
            client.delete_alert_policy(name=name)

            return json.dumps(
                {
                    "status": "success",
                    "message": f"Alert policy {alert_id} successfully deleted",
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def create_notification_channel(
        display_name: str,
        channel_type: str,
        labels: Dict[str, str],
        project_id: str = None,
        description: str = "",
        enabled: bool = True,
    ) -> str:
        """
        Create a notification channel

        Args:
            display_name: Human-readable name for the channel
            channel_type: Type of channel (email, sms, slack, pagerduty, etc.)
            labels: Channel-specific configuration (e.g., {"email_address": "user@example.com"})
            project_id: GCP project ID (defaults to configured project)
            description: Optional description for the channel
            enabled: Whether the channel should be enabled
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().monitoring
            project_id = project_id or client_instances.get_project_id()

            # Create notification channel
            notification_channel = monitoring_v3.NotificationChannel(
                type=channel_type,
                display_name=display_name,
                description=description,
                labels=labels,
                enabled=monitoring_v3.BoolValue(value=enabled),
            )

            # Create the request
            request = monitoring_v3.CreateNotificationChannelRequest(
                name=f"projects/{project_id}", notification_channel=notification_channel
            )

            print(f"Creating notification channel: {display_name} ({channel_type})...")
            response = client.create_notification_channel(request=request)

            return json.dumps(
                {
                    "status": "success",
                    "name": response.name,
                    "type": response.type,
                    "display_name": response.display_name,
                    "description": response.description,
                    "verification_status": monitoring_v3.NotificationChannel.VerificationStatus.Name(
                        response.verification_status
                    )
                    if response.verification_status
                    else None,
                    "enabled": response.enabled,
                    "labels": dict(response.labels) if response.labels else {},
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    # Prompts
    @mcp_instance.prompt()
    def create_alert_prompt() -> str:
        """Prompt for creating a new alert policy"""
        return """
I need to create a new alert policy in Cloud Monitoring.

Please help me with:
1. Selecting the appropriate metric type for my alert
2. Setting up sensible thresholds and durations
3. Understanding the different comparison types
4. Best practices for alert documentation
5. Setting up notification channels

I'd like to create an alert that triggers when:
"""

    @mcp_instance.prompt()
    def monitor_resources_prompt() -> str:
        """Prompt for guidance on monitoring GCP resources"""
        return """
I need to set up monitoring for my GCP resources. Please help me understand:

1. What are the most important metrics I should be monitoring for:
   - Compute Engine instances
   - Cloud SQL databases
   - Cloud Storage buckets
   - App Engine applications
   - Kubernetes Engine clusters

2. What are recommended thresholds for alerts on these resources?

3. How should I organize my monitoring to keep it manageable?

4. What visualization options do I have in Cloud Monitoring?
"""
