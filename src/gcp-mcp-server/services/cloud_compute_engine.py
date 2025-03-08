import json
from typing import Optional

from services import client_instances


def register(mcp_instance):
    """Register all Compute Engine resources and tools with the MCP instance."""

    # Resources
    @mcp_instance.resource("gcp://compute/{project_id}/{zone}/instances")
    def list_instances_resource(project_id: str = None, zone: str = None) -> str:
        """List all Compute Engine instances in a zone"""
        try:
            # Get client from client_instances
            client = client_instances.get_clients().compute
            project_id = project_id or client_instances.get_project_id()
            zone = zone or client_instances.get_location()

            instance_list = client.list(project=project_id, zone=zone)
            result = []
            for instance in instance_list:
                result.append(
                    {
                        "name": instance.name,
                        "status": instance.status,
                        "machine_type": instance.machine_type.split("/")[-1]
                        if instance.machine_type
                        else None,
                        "internal_ip": instance.network_interfaces[0].network_i_p
                        if instance.network_interfaces
                        and len(instance.network_interfaces) > 0
                        else None,
                        "creation_timestamp": instance.creation_timestamp,
                    }
                )
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    # Tools
    @mcp_instance.tool()
    def create_instance(
        instance_name: str,
        machine_type: str,
        project_id: str = None,
        zone: str = None,
        image: str = "projects/debian-cloud/global/images/family/debian-11",
        network: str = "global/networks/default",
        disk_size_gb: int = 10,
    ) -> str:
        """
        Create a new Compute Engine instance

        Args:
            instance_name: Name for the new instance
            machine_type: Machine type (e.g., n2-standard-2)
            project_id: GCP project ID (defaults to configured project)
            zone: GCP zone (defaults to configured location)
            image: Source image for boot disk
            network: Network to connect to
            disk_size_gb: Size of boot disk in GB
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().compute
            project_id = project_id or client_instances.get_project_id()
            zone = zone or client_instances.get_location()

            # Build instance configuration
            instance_config = {
                "name": instance_name,
                "machine_type": f"zones/{zone}/machineTypes/{machine_type}",
                "disks": [
                    {
                        "boot": True,
                        "auto_delete": True,
                        "initialize_params": {
                            "source_image": image,
                            "disk_size_gb": disk_size_gb,
                        },
                    }
                ],
                "network_interfaces": [
                    {
                        "network": network,
                        "access_configs": [
                            {"type": "ONE_TO_ONE_NAT", "name": "External NAT"}
                        ],
                    }
                ],
            }

            print(f"Creating instance {instance_name} in {zone}...")
            operation = client.insert(
                project=project_id, zone=zone, instance_resource=instance_config
            )

            # Wait for operation to complete
            operation.result()
            return json.dumps(
                {
                    "status": "success",
                    "instance_name": instance_name,
                    "zone": zone,
                    "operation_type": "insert",
                    "operation_status": "DONE",
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def list_instances(
        project_id: str = None,
        zone: str = None,
        filter: Optional[str] = None,
    ) -> str:
        """
        List Compute Engine instances in a zone

        Args:
            project_id: GCP project ID (defaults to configured project)
            zone: GCP zone (defaults to configured location)
            filter: Optional filter expression (e.g., "status=RUNNING")
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().compute
            project_id = project_id or client_instances.get_project_id()
            zone = zone or client_instances.get_location()

            instance_list = client.list(project=project_id, zone=zone, filter=filter)

            instances = []
            for instance in instance_list:
                instances.append(
                    {
                        "name": instance.name,
                        "status": instance.status,
                        "machine_type": instance.machine_type.split("/")[-1]
                        if instance.machine_type
                        else None,
                        "internal_ip": instance.network_interfaces[0].network_i_p
                        if instance.network_interfaces
                        and len(instance.network_interfaces) > 0
                        else None,
                        "creation_timestamp": instance.creation_timestamp,
                    }
                )

            return json.dumps(
                {"status": "success", "instances": instances, "count": len(instances)},
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def start_instance(
        instance_name: str,
        project_id: str = None,
        zone: str = None,
    ) -> str:
        """
        Start a stopped Compute Engine instance

        Args:
            instance_name: Name of the instance to start
            project_id: GCP project ID (defaults to configured project)
            zone: GCP zone (defaults to configured location)
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().compute
            project_id = project_id or client_instances.get_project_id()
            zone = zone or client_instances.get_location()

            print(f"Starting instance {instance_name}...")
            operation = client.start(
                project=project_id, zone=zone, instance=instance_name
            )
            operation.result()

            return json.dumps(
                {
                    "status": "success",
                    "instance_name": instance_name,
                    "operation_status": "DONE",
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def stop_instance(
        instance_name: str,
        project_id: str = None,
        zone: str = None,
    ) -> str:
        """
        Stop a running Compute Engine instance

        Args:
            instance_name: Name of the instance to stop
            project_id: GCP project ID (defaults to configured project)
            zone: GCP zone (defaults to configured location)
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().compute
            project_id = project_id or client_instances.get_project_id()
            zone = zone or client_instances.get_location()

            print(f"Stopping instance {instance_name}...")
            operation = client.stop(
                project=project_id, zone=zone, instance=instance_name
            )
            operation.result()

            return json.dumps(
                {
                    "status": "success",
                    "instance_name": instance_name,
                    "operation_status": "DONE",
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def delete_instance(
        instance_name: str,
        project_id: str = None,
        zone: str = None,
    ) -> str:
        """
        Delete a Compute Engine instance

        Args:
            instance_name: Name of the instance to delete
            project_id: GCP project ID (defaults to configured project)
            zone: GCP zone (defaults to configured location)
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().compute
            project_id = project_id or client_instances.get_project_id()
            zone = zone or client_instances.get_location()

            print(f"Deleting instance {instance_name}...")
            operation = client.delete(
                project=project_id, zone=zone, instance=instance_name
            )
            operation.result()

            return json.dumps(
                {
                    "status": "success",
                    "instance_name": instance_name,
                    "operation_status": "DONE",
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    # Prompts
    @mcp_instance.prompt()
    def instance_config_prompt(workload_type: str = "web-server") -> str:
        """Prompt for creating Compute Engine configurations"""
        return f"""
I need to configure a Compute Engine instance for {workload_type}. Please help with:

1. Recommended machine types for {workload_type}
2. Disk type and size recommendations
3. Network configuration best practices
4. Security considerations (service accounts, firewall rules)
5. Cost optimization strategies
"""

    @mcp_instance.prompt()
    def troubleshooting_prompt(issue: str = "instance not responding") -> str:
        """Prompt for troubleshooting Compute Engine issues"""
        return f"""
I'm experiencing {issue} with my Compute Engine instance. Please guide me through:

1. Common causes for this issue
2. Diagnostic steps using Cloud Console and CLI
3. Log analysis techniques
4. Recovery procedures
5. Prevention strategies
"""
