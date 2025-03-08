import json

from google.cloud import logging_v2
from services import client_instances


def register(mcp_instance):
    """Register all Cloud Audit Logs resources and tools with the MCP instance."""

    # Resources
    @mcp_instance.resource("gcp://audit-logs/{project_id}")
    def list_audit_logs_resource(project_id: str = None) -> str:
        """List recent audit logs from a specific project"""
        try:
            # Get client from client_instances
            client = client_instances.get_clients().logging
            project_id = project_id or client_instances.get_project_id()

            # Filter for audit logs only
            filter_str = 'logName:"cloudaudit.googleapis.com"'

            # List log entries
            entries = client.list_log_entries(
                request={
                    "resource_names": [f"projects/{project_id}"],
                    "filter": filter_str,
                    "page_size": 10,  # Limiting to 10 for responsiveness
                }
            )

            result = []
            for entry in entries:
                log_data = {
                    "timestamp": entry.timestamp.isoformat()
                    if entry.timestamp
                    else None,
                    "severity": entry.severity.name if entry.severity else None,
                    "log_name": entry.log_name,
                    "resource": {
                        "type": entry.resource.type,
                        "labels": dict(entry.resource.labels)
                        if entry.resource.labels
                        else {},
                    }
                    if entry.resource
                    else {},
                }

                # Handle payload based on type
                if hasattr(entry, "json_payload") and entry.json_payload:
                    log_data["payload"] = dict(entry.json_payload)
                elif hasattr(entry, "proto_payload") and entry.proto_payload:
                    log_data["payload"] = "Proto payload (details omitted)"
                elif hasattr(entry, "text_payload") and entry.text_payload:
                    log_data["payload"] = entry.text_payload

                result.append(log_data)

            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    @mcp_instance.resource("gcp://audit-logs/{project_id}/sinks")
    def list_log_sinks_resource(project_id: str = None) -> str:
        """List log sinks configured for a project"""
        try:
            # Get client from client_instances
            client = client_instances.get_clients().logging
            project_id = project_id or client_instances.get_project_id()

            parent = f"projects/{project_id}"
            sinks = client.list_sinks(parent=parent)

            result = []
            for sink in sinks:
                result.append(
                    {
                        "name": sink.name,
                        "destination": sink.destination,
                        "filter": sink.filter,
                        "description": sink.description,
                        "disabled": sink.disabled,
                    }
                )

            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    # Tools
    @mcp_instance.tool()
    def list_audit_logs(
        project_id: str = None,
        filter_str: str = 'logName:"cloudaudit.googleapis.com"',
        page_size: int = 20,
    ) -> str:
        """
        List Google Cloud Audit logs from a project

        Args:
            project_id: GCP project ID (defaults to configured project)
            filter_str: Log filter expression (defaults to audit logs)
            page_size: Maximum number of entries to return
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().logging
            project_id = project_id or client_instances.get_project_id()

            print(f"Retrieving audit logs from project {project_id}...")

            # List log entries
            entries = client.list_log_entries(
                request={
                    "resource_names": [f"projects/{project_id}"],
                    "filter": filter_str,
                    "page_size": page_size,
                }
            )

            result = []
            for entry in entries:
                log_data = {
                    "timestamp": entry.timestamp.isoformat()
                    if entry.timestamp
                    else None,
                    "severity": entry.severity.name if entry.severity else None,
                    "log_name": entry.log_name,
                    "resource": {
                        "type": entry.resource.type,
                        "labels": dict(entry.resource.labels)
                        if entry.resource.labels
                        else {},
                    }
                    if entry.resource
                    else {},
                }

                # Handle payload based on type
                if hasattr(entry, "json_payload") and entry.json_payload:
                    log_data["payload"] = dict(entry.json_payload)
                elif hasattr(entry, "proto_payload") and entry.proto_payload:
                    log_data["payload"] = "Proto payload (details omitted)"
                elif hasattr(entry, "text_payload") and entry.text_payload:
                    log_data["payload"] = entry.text_payload

                result.append(log_data)

            return json.dumps(
                {
                    "status": "success",
                    "entries": result,
                    "count": len(result),
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def filter_admin_activity_logs(
        project_id: str = None,
        service_name: str = "",
        resource_type: str = "",
        time_range: str = "1h",
        page_size: int = 20,
    ) -> str:
        """
        Filter Admin Activity audit logs for specific services or resource types

        Args:
            project_id: GCP project ID (defaults to configured project)
            service_name: Optional service name to filter by (e.g., compute.googleapis.com)
            resource_type: Optional resource type to filter by (e.g., gce_instance)
            time_range: Time range for logs (e.g., 1h, 24h, 7d)
            page_size: Maximum number of entries to return
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().logging
            project_id = project_id or client_instances.get_project_id()

            # Build filter string
            filter_parts = ['logName:"cloudaudit.googleapis.com%2Factivity"']

            if service_name:
                filter_parts.append(f'protoPayload.serviceName="{service_name}"')

            if resource_type:
                filter_parts.append(f'resource.type="{resource_type}"')

            if time_range:
                filter_parts.append(f'timestamp >= "-{time_range}"')

            filter_str = " AND ".join(filter_parts)

            print(f"Filtering Admin Activity logs with: {filter_str}")

            # List log entries
            entries = client.list_log_entries(
                request={
                    "resource_names": [f"projects/{project_id}"],
                    "filter": filter_str,
                    "page_size": page_size,
                }
            )

            result = []
            for entry in entries:
                # Extract relevant fields for admin activity logs
                log_data = {
                    "timestamp": entry.timestamp.isoformat()
                    if entry.timestamp
                    else None,
                    "method_name": None,
                    "resource_name": None,
                    "service_name": None,
                    "user": None,
                }

                # Extract data from proto payload
                if hasattr(entry, "proto_payload") and entry.proto_payload:
                    payload = entry.proto_payload
                    if hasattr(payload, "method_name"):
                        log_data["method_name"] = payload.method_name
                    if hasattr(payload, "resource_name"):
                        log_data["resource_name"] = payload.resource_name
                    if hasattr(payload, "service_name"):
                        log_data["service_name"] = payload.service_name

                    # Extract authentication info
                    if hasattr(payload, "authentication_info"):
                        auth_info = payload.authentication_info
                        if hasattr(auth_info, "principal_email"):
                            log_data["user"] = auth_info.principal_email

                result.append(log_data)

            return json.dumps(
                {
                    "status": "success",
                    "entries": result,
                    "count": len(result),
                    "filter": filter_str,
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def create_log_sink(
        sink_name: str,
        destination: str,
        project_id: str = None,
        filter_str: str = 'logName:"cloudaudit.googleapis.com"',
        description: str = "",
    ) -> str:
        """
        Create a log sink to export audit logs to a destination

        Args:
            sink_name: Name for the new log sink
            destination: Destination for logs (e.g., storage.googleapis.com/my-bucket)
            project_id: GCP project ID (defaults to configured project)
            filter_str: Log filter expression (defaults to audit logs)
            description: Optional description for the sink
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().logging
            project_id = project_id or client_instances.get_project_id()

            parent = f"projects/{project_id}"

            # Create sink configuration
            sink = logging_v2.LogSink(
                name=sink_name,
                destination=destination,
                filter=filter_str,
                description=description,
            )

            print(f"Creating log sink '{sink_name}' to export to {destination}...")

            # Create the sink
            response = client.create_sink(
                request={
                    "parent": parent,
                    "sink": sink,
                }
            )

            # Important: Recommend setting up IAM permissions
            writer_identity = response.writer_identity

            return json.dumps(
                {
                    "status": "success",
                    "name": response.name,
                    "destination": response.destination,
                    "filter": response.filter,
                    "writer_identity": writer_identity,
                    "next_steps": f"Important: Grant {writer_identity} the appropriate permissions on the destination",
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    # Prompts
    @mcp_instance.prompt()
    def audit_log_investigation() -> str:
        """Prompt for investigating security incidents through audit logs"""
        return """
I need to investigate a potential security incident in my Google Cloud project.

Please help me:
1. Determine what types of audit logs I should check (Admin Activity, Data Access, System Event)
2. Create an effective filter query to find relevant logs
3. Identify key fields to examine for signs of unusual activity
4. Suggest common indicators of potential security issues in audit logs
"""

    @mcp_instance.prompt()
    def log_export_setup() -> str:
        """Prompt for setting up log exports for compliance"""
        return """
I need to set up log exports for compliance requirements.

Please help me:
1. Understand the different destinations available for log exports
2. Design an effective filter to capture all required audit events
3. Implement a log sink with appropriate permissions
4. Verify my setup is correctly capturing and exporting logs
"""
