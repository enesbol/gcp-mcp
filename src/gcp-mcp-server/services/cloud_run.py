import json
from typing import Dict, Optional

from google.cloud import run_v2
from google.protobuf import field_mask_pb2
from services import client_instances


def register(mcp_instance):
    """Register all Cloud Run resources and tools with the MCP instance."""

    # Resources
    @mcp_instance.resource("gcp://cloudrun/{project_id}/{region}/services")
    def list_services_resource(project_id: str = None, region: str = None) -> str:
        """List all Cloud Run services in a specific region"""
        try:
            # Get client from client_instances
            client = client_instances.get_clients().run
            project_id = project_id or client_instances.get_project_id()
            region = region or client_instances.get_location()

            parent = f"projects/{project_id}/locations/{region}"
            services = client.list_services(parent=parent)

            result = []
            for service in services:
                result.append(
                    {
                        "name": service.name.split("/")[-1],
                        "uid": service.uid,
                        "generation": service.generation,
                        "labels": dict(service.labels) if service.labels else {},
                        "annotations": dict(service.annotations)
                        if service.annotations
                        else {},
                        "create_time": service.create_time.isoformat()
                        if service.create_time
                        else None,
                        "update_time": service.update_time.isoformat()
                        if service.update_time
                        else None,
                        "uri": service.uri,
                    }
                )

            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    @mcp_instance.resource("gcp://run/{project_id}/{location}/service/{service_name}")
    def get_service_resource(
        service_name: str, project_id: str = None, location: str = None
    ) -> str:
        """Get details for a specific Cloud Run service"""
        try:
            # Get client from client_instances
            client = client_instances.get_clients().run
            project_id = project_id or client_instances.get_project_id()
            location = location or client_instances.get_location()

            name = f"projects/{project_id}/locations/{location}/services/{service_name}"
            service = client.get_service(name=name)

            # Extract container details
            containers = []
            if service.template and service.template.containers:
                for container in service.template.containers:
                    container_info = {
                        "image": container.image,
                        "command": list(container.command) if container.command else [],
                        "args": list(container.args) if container.args else [],
                        "env": [
                            {"name": env.name, "value": env.value}
                            for env in container.env
                        ]
                        if container.env
                        else [],
                        "resources": {
                            "limits": dict(container.resources.limits)
                            if container.resources and container.resources.limits
                            else {},
                            "cpu_idle": container.resources.cpu_idle
                            if container.resources
                            else None,
                        }
                        if container.resources
                        else {},
                        "ports": [
                            {"name": port.name, "container_port": port.container_port}
                            for port in container.ports
                        ]
                        if container.ports
                        else [],
                    }
                    containers.append(container_info)

            # Extract scaling details
            scaling = None
            if service.template and service.template.scaling:
                scaling = {
                    "min_instance_count": service.template.scaling.min_instance_count,
                    "max_instance_count": service.template.scaling.max_instance_count,
                }

            result = {
                "name": service.name.split("/")[-1],
                "uid": service.uid,
                "generation": service.generation,
                "labels": dict(service.labels) if service.labels else {},
                "annotations": dict(service.annotations) if service.annotations else {},
                "create_time": service.create_time.isoformat()
                if service.create_time
                else None,
                "update_time": service.update_time.isoformat()
                if service.update_time
                else None,
                "creator": service.creator,
                "last_modifier": service.last_modifier,
                "client": service.client,
                "client_version": service.client_version,
                "ingress": service.ingress.name if service.ingress else None,
                "launch_stage": service.launch_stage.name
                if service.launch_stage
                else None,
                "traffic": [
                    {
                        "type": traffic.type_.name if traffic.type_ else None,
                        "revision": traffic.revision.split("/")[-1]
                        if traffic.revision
                        else None,
                        "percent": traffic.percent,
                        "tag": traffic.tag,
                    }
                    for traffic in service.traffic
                ]
                if service.traffic
                else [],
                "uri": service.uri,
                "template": {
                    "containers": containers,
                    "execution_environment": service.template.execution_environment.name
                    if service.template and service.template.execution_environment
                    else None,
                    "vpc_access": {
                        "connector": service.template.vpc_access.connector,
                        "egress": service.template.vpc_access.egress.name
                        if service.template.vpc_access.egress
                        else None,
                    }
                    if service.template and service.template.vpc_access
                    else None,
                    "scaling": scaling,
                    "timeout": f"{service.template.timeout.seconds}s {service.template.timeout.nanos}ns"
                    if service.template and service.template.timeout
                    else None,
                    "service_account": service.template.service_account
                    if service.template
                    else None,
                }
                if service.template
                else {},
            }

            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    @mcp_instance.resource(
        "gcp://run/{project_id}/{location}/service/{service_name}/revisions"
    )
    def list_revisions_resource(
        service_name: str, project_id: str = None, location: str = None
    ) -> str:
        """List revisions for a specific Cloud Run service"""
        try:
            # Get client from client_instances
            client = client_instances.get_clients().run
            project_id = project_id or client_instances.get_project_id()
            location = location or client_instances.get_location()

            parent = f"projects/{project_id}/locations/{location}"

            # List all revisions
            revisions = client.list_revisions(parent=parent)

            # Filter revisions for the specified service
            service_revisions = []
            for revision in revisions:
                # Check if this revision belongs to the specified service
                if service_name in revision.name:
                    service_revisions.append(
                        {
                            "name": revision.name.split("/")[-1],
                            "uid": revision.uid,
                            "generation": revision.generation,
                            "service": revision.service.split("/")[-1]
                            if revision.service
                            else None,
                            "create_time": revision.create_time.isoformat()
                            if revision.create_time
                            else None,
                            "update_time": revision.update_time.isoformat()
                            if revision.update_time
                            else None,
                            "scaling": {
                                "min_instance_count": revision.scaling.min_instance_count
                                if revision.scaling
                                else None,
                                "max_instance_count": revision.scaling.max_instance_count
                                if revision.scaling
                                else None,
                            }
                            if revision.scaling
                            else None,
                            "conditions": [
                                {
                                    "type": condition.type,
                                    "state": condition.state.name
                                    if condition.state
                                    else None,
                                    "message": condition.message,
                                    "last_transition_time": condition.last_transition_time.isoformat()
                                    if condition.last_transition_time
                                    else None,
                                    "severity": condition.severity.name
                                    if condition.severity
                                    else None,
                                }
                                for condition in revision.conditions
                            ]
                            if revision.conditions
                            else [],
                        }
                    )

            return json.dumps(service_revisions, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    # Tools
    @mcp_instance.tool()
    def create_service(
        service_name: str,
        image: str,
        project_id: str = None,
        location: str = None,
        env_vars: Optional[Dict[str, str]] = None,
        memory_limit: str = "512Mi",
        cpu_limit: str = "1",
        min_instances: int = 0,
        max_instances: int = 100,
        port: int = 8080,
        allow_unauthenticated: bool = True,
        service_account: str = None,
        vpc_connector: str = None,
        timeout_seconds: int = 300,
    ) -> str:
        """
        Create a new Cloud Run service

        Args:
            service_name: Name for the new service
            image: Container image to deploy (e.g., gcr.io/project/image:tag)
            project_id: GCP project ID (defaults to configured project)
            location: GCP region (e.g., us-central1) (defaults to configured location)
            env_vars: Environment variables as key-value pairs
            memory_limit: Memory limit (e.g., 512Mi, 1Gi)
            cpu_limit: CPU limit (e.g., 1, 2)
            min_instances: Minimum number of instances
            max_instances: Maximum number of instances
            port: Container port
            allow_unauthenticated: Whether to allow unauthenticated access
            service_account: Service account email
            vpc_connector: VPC connector name
            timeout_seconds: Request timeout in seconds
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().run
            project_id = project_id or client_instances.get_project_id()
            location = location or client_instances.get_location()

            print(f"Creating Cloud Run service {service_name} in {location}...")

            # Create container
            container = run_v2.Container(
                image=image,
                resources=run_v2.ResourceRequirements(
                    limits={
                        "memory": memory_limit,
                        "cpu": cpu_limit,
                    }
                ),
            )

            # Add environment variables if provided
            if env_vars:
                container.env = [
                    run_v2.EnvVar(name=key, value=value)
                    for key, value in env_vars.items()
                ]

            # Add port
            container.ports = [run_v2.ContainerPort(container_port=port)]

            # Create template
            template = run_v2.RevisionTemplate(
                containers=[container],
                scaling=run_v2.RevisionScaling(
                    min_instance_count=min_instances,
                    max_instance_count=max_instances,
                ),
                timeout=run_v2.Duration(seconds=timeout_seconds),
            )

            # Add service account if provided
            if service_account:
                template.service_account = service_account

            # Add VPC connector if provided
            if vpc_connector:
                template.vpc_access = run_v2.VpcAccess(
                    connector=vpc_connector,
                    egress=run_v2.VpcAccess.VpcEgress.ALL_TRAFFIC,
                )

            # Create service
            service = run_v2.Service(
                template=template,
                ingress=run_v2.IngressTraffic.INGRESS_TRAFFIC_ALL
                if allow_unauthenticated
                else run_v2.IngressTraffic.INGRESS_TRAFFIC_INTERNAL_ONLY,
            )

            # Create the service
            parent = f"projects/{project_id}/locations/{location}"
            operation = client.create_service(
                parent=parent,
                service_id=service_name,
                service=service,
            )

            # Wait for the operation to complete
            print(f"Waiting for service {service_name} to be created...")
            result = operation.result()

            return json.dumps(
                {
                    "status": "success",
                    "name": result.name.split("/")[-1],
                    "uri": result.uri,
                    "create_time": result.create_time.isoformat()
                    if result.create_time
                    else None,
                    "update_time": result.update_time.isoformat()
                    if result.update_time
                    else None,
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def list_services(project_id: str = None, region: str = None) -> str:
        """
        List Cloud Run services in a specific region

        Args:
            project_id: GCP project ID (defaults to configured project)
            region: GCP region (e.g., us-central1) (defaults to configured location)
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().run
            project_id = project_id or client_instances.get_project_id()
            region = region or client_instances.get_location()

            parent = f"projects/{project_id}/locations/{region}"

            print(f"Listing Cloud Run services in {region}...")
            services = client.list_services(parent=parent)

            result = []
            for service in services:
                result.append(
                    {
                        "name": service.name.split("/")[-1],
                        "uri": service.uri,
                        "create_time": service.create_time.isoformat()
                        if service.create_time
                        else None,
                        "update_time": service.update_time.isoformat()
                        if service.update_time
                        else None,
                        "labels": dict(service.labels) if service.labels else {},
                    }
                )

            return json.dumps(
                {"status": "success", "services": result, "count": len(result)},
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def update_service(
        service_name: str,
        project_id: str = None,
        region: str = None,
        image: Optional[str] = None,
        memory: Optional[str] = None,
        cpu: Optional[str] = None,
        max_instances: Optional[int] = None,
        min_instances: Optional[int] = None,
        env_vars: Optional[Dict[str, str]] = None,
        concurrency: Optional[int] = None,
        timeout_seconds: Optional[int] = None,
        service_account: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Update an existing Cloud Run service

        Args:
            service_name: Name of the service to update
            project_id: GCP project ID (defaults to configured project)
            region: GCP region (e.g., us-central1) (defaults to configured location)
            image: New container image URL (optional)
            memory: New memory allocation (optional)
            cpu: New CPU allocation (optional)
            max_instances: New maximum number of instances (optional)
            min_instances: New minimum number of instances (optional)
            env_vars: New environment variables (optional)
            concurrency: New maximum concurrent requests per instance (optional)
            timeout_seconds: New request timeout in seconds (optional)
            service_account: New service account email (optional)
            labels: New key-value labels to apply to the service (optional)
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().run
            project_id = project_id or client_instances.get_project_id()
            region = region or client_instances.get_location()

            # Get the existing service
            name = f"projects/{project_id}/locations/{region}/services/{service_name}"

            print(f"Getting current service configuration for {service_name}...")
            service = client.get_service(name=name)

            # Track which fields are being updated
            update_mask_fields = []

            # Update the container image if specified
            if image and service.template and service.template.containers:
                service.template.containers[0].image = image
                update_mask_fields.append("template.containers[0].image")

            # Update resources if specified
            if (memory or cpu) and service.template and service.template.containers:
                if not service.template.containers[0].resources:
                    service.template.containers[
                        0
                    ].resources = run_v2.ResourceRequirements(limits={})

                if not service.template.containers[0].resources.limits:
                    service.template.containers[0].resources.limits = {}

                if memory:
                    service.template.containers[0].resources.limits["memory"] = memory
                    update_mask_fields.append(
                        "template.containers[0].resources.limits.memory"
                    )

                if cpu:
                    service.template.containers[0].resources.limits["cpu"] = cpu
                    update_mask_fields.append(
                        "template.containers[0].resources.limits.cpu"
                    )

            # Update scaling parameters
            if max_instances is not None and service.template:
                service.template.max_instance_count = max_instances
                update_mask_fields.append("template.max_instance_count")

            if min_instances is not None and service.template:
                service.template.min_instance_count = min_instances
                update_mask_fields.append("template.min_instance_count")

            # Update concurrency
            if concurrency is not None and service.template:
                service.template.max_instance_request_concurrency = concurrency
                update_mask_fields.append("template.max_instance_request_concurrency")

            # Update timeout
            if timeout_seconds is not None and service.template:
                service.template.timeout = {"seconds": timeout_seconds}
                update_mask_fields.append("template.timeout")

            # Update service account
            if service_account is not None and service.template:
                service.template.service_account = service_account
                update_mask_fields.append("template.service_account")

            # Update environment variables
            if (
                env_vars is not None
                and service.template
                and service.template.containers
            ):
                # Create new env var list
                new_env_vars = [
                    run_v2.EnvVar(name=key, value=value)
                    for key, value in env_vars.items()
                ]
                service.template.containers[0].env = new_env_vars
                update_mask_fields.append("template.containers[0].env")

            # Update labels
            if labels is not None:
                service.labels = labels
                update_mask_fields.append("labels")

            # Only proceed if there are fields to update
            if not update_mask_fields:
                return json.dumps(
                    {"status": "info", "message": "No updates specified"}, indent=2
                )

            # Create update mask
            update_mask = field_mask_pb2.FieldMask(paths=update_mask_fields)

            # Create the request
            request = run_v2.UpdateServiceRequest(
                service=service, update_mask=update_mask
            )

            print(f"Updating Cloud Run service {service_name}...")
            operation = client.update_service(request=request)

            print("Waiting for service update to complete...")
            response = operation.result()

            return json.dumps(
                {
                    "status": "success",
                    "name": response.name,
                    "uri": response.uri,
                    "updated_fields": update_mask_fields,
                    "conditions": [
                        {
                            "type": condition.type_,
                            "state": condition.state.name
                            if hasattr(condition.state, "name")
                            else str(condition.state),
                            "message": condition.message,
                        }
                        for condition in response.conditions
                    ]
                    if response.conditions
                    else [],
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def delete_service(
        service_name: str, project_id: str = None, region: str = None
    ) -> str:
        """
        Delete a Cloud Run service

        Args:
            service_name: Name of the service to delete
            project_id: GCP project ID (defaults to configured project)
            region: GCP region (e.g., us-central1) (defaults to configured location)
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().run
            project_id = project_id or client_instances.get_project_id()
            region = region or client_instances.get_location()

            name = f"projects/{project_id}/locations/{region}/services/{service_name}"

            print(f"Deleting Cloud Run service {service_name} in {region}...")
            operation = client.delete_service(name=name)

            print("Waiting for service deletion to complete...")
            operation.result()

            return json.dumps(
                {
                    "status": "success",
                    "message": f"Service {service_name} successfully deleted",
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def get_service(
        service_name: str, project_id: str = None, region: str = None
    ) -> str:
        """
        Get details of a specific Cloud Run service

        Args:
            service_name: Name of the service
            project_id: GCP project ID (defaults to configured project)
            region: GCP region (e.g., us-central1) (defaults to configured location)
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().run
            project_id = project_id or client_instances.get_project_id()
            region = region or client_instances.get_location()

            name = f"projects/{project_id}/locations/{region}/services/{service_name}"

            print(f"Getting details for Cloud Run service {service_name}...")
            service = client.get_service(name=name)

            # Parse container details
            containers = []
            if service.template and service.template.containers:
                for container in service.template.containers:
                    container_info = {
                        "image": container.image,
                        "resources": {
                            "limits": dict(container.resources.limits)
                            if container.resources and container.resources.limits
                            else {}
                        }
                        if container.resources
                        else {},
                        "env_vars": {env.name: env.value for env in container.env}
                        if container.env
                        else {},
                    }
                    containers.append(container_info)

            # Parse traffic
            traffic_result = []
            if service.traffic:
                for traffic in service.traffic:
                    traffic_info = {
                        "type": traffic.type_.name
                        if hasattr(traffic.type_, "name")
                        else str(traffic.type_),
                        "revision": traffic.revision.split("/")[-1]
                        if traffic.revision
                        else None,
                        "percent": traffic.percent,
                        "tag": traffic.tag,
                    }
                    traffic_result.append(traffic_info)

            return json.dumps(
                {
                    "status": "success",
                    "name": service.name.split("/")[-1],
                    "uri": service.uri,
                    "containers": containers,
                    "traffic": traffic_result,
                    "update_time": service.update_time.isoformat()
                    if service.update_time
                    else None,
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    # Prompts
    @mcp_instance.prompt()
    def deploy_service_prompt(
        service_name: str,
        image: str,
        min_instances: str = "0",
        max_instances: str = "100",
        env_vars: str = "{}",
    ) -> str:
        """Prompt to deploy a Cloud Run service with the given configuration"""
        return f"""
I need to deploy a Cloud Run service with the following configuration:

- Service name: {service_name}
- Container image: {image}
- Min instances: {min_instances}
- Max instances: {max_instances}
- Environment variables: {env_vars}

Please help me set up this service and explain the deployment process and any best practices I should follow.
"""

    @mcp_instance.prompt()
    def check_service_status_prompt(service_name: str) -> str:
        """Prompt to check the status of a deployed Cloud Run service"""
        return f"""
I need to check the current status of my Cloud Run service named "{service_name}".

Please provide me with:
1. Is the service currently running?
2. What is the URL to access it?
3. What revision is currently serving traffic?
4. Are there any issues with the service?
"""

    @mcp_instance.prompt()
    def create_service_prompt(region: str = "us-central1") -> str:
        """Prompt for creating a new Cloud Run service"""
        return f"""
I need to create a new Cloud Run service in {region}.

Please help me with:
1. What container image should I use?
2. How much CPU and memory should I allocate?
3. Should I set min and max instances for scaling?
4. Do I need to set any environment variables?
5. Should I allow unauthenticated access?
6. What's the best way to deploy my service?
"""

    @mcp_instance.prompt()
    def update_service_prompt() -> str:
        """Prompt for updating a Cloud Run service"""
        return """
I need to update my Cloud Run service.

Please help me understand:
1. How to update the container image
2. How to change resource allocations
3. How to add or modify environment variables
4. How to update scaling settings
5. Best practices for zero-downtime updates
"""
