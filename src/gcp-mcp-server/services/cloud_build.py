import json
from typing import Dict, Optional

from services import client_instances


def register(mcp_instance):
    """Register all Cloud Build resources and tools with the MCP instance."""

    # Resources
    @mcp_instance.resource("gcp://cloudbuild/{project_id}/builds")
    def list_builds_resource(project_id: str = None) -> str:
        """List all Cloud Build executions for a project"""
        try:
            # Get client from client_instances
            client = client_instances.get_clients().cloudbuild
            project_id = project_id or client_instances.get_project_id()

            builds = client.list_builds(project_id=project_id)
            result = []
            for build in builds:
                result.append(
                    {
                        "id": build.id,
                        "status": build.status.name if build.status else None,
                        "source": build.source.repo_source.commit_sha
                        if build.source and build.source.repo_source
                        else None,
                        "create_time": build.create_time.isoformat()
                        if build.create_time
                        else None,
                        "logs_url": build.logs_url,
                        "substitutions": dict(build.substitutions)
                        if build.substitutions
                        else {},
                    }
                )
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    @mcp_instance.resource("gcp://cloudbuild/{project_id}/triggers")
    def list_triggers_resource(project_id: str = None) -> str:
        """List all Cloud Build triggers for a project"""
        try:
            # Get client from client_instances
            client = client_instances.get_clients().cloudbuild
            project_id = project_id or client_instances.get_project_id()

            triggers = client.list_triggers(project_id=project_id)
            result = []
            for trigger in triggers:
                result.append(
                    {
                        "id": trigger.id,
                        "name": trigger.name,
                        "description": trigger.description,
                        "trigger_template": {
                            "repo_name": trigger.trigger_template.repo_name,
                            "branch_name": trigger.trigger_template.branch_name,
                        }
                        if trigger.trigger_template
                        else None,
                    }
                )
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    # Tools
    @mcp_instance.tool()
    def trigger_build(
        build_config: Dict,
        project_id: str = None,
    ) -> str:
        """
        Trigger a new Cloud Build execution

        Args:
            build_config: Dictionary containing the build configuration
            project_id: GCP project ID (defaults to configured project)
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().cloudbuild
            project_id = project_id or client_instances.get_project_id()

            # Convert config dict to Build object
            build = cloudbuild_v1.Build.from_json(json.dumps(build_config))

            print(f"Triggering build in project {project_id}...")
            operation = client.create_build(project_id=project_id, build=build)
            response = operation.result()

            return json.dumps(
                {
                    "status": "success",
                    "build_id": response.id,
                    "status": response.status.name if response.status else None,
                    "logs_url": response.logs_url,
                    "build_name": response.name,
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def list_builds(
        project_id: str = None,
        filter: Optional[str] = None,
        page_size: Optional[int] = 100,
    ) -> str:
        """
        List Cloud Build executions with optional filtering

        Args:
            project_id: GCP project ID (defaults to configured project)
            filter: Filter expression for builds
            page_size: Maximum number of results to return
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().cloudbuild
            project_id = project_id or client_instances.get_project_id()

            request = cloudbuild_v1.ListBuildsRequest(
                project_id=project_id, filter=filter, page_size=page_size
            )

            builds = []
            for build in client.list_builds(request=request):
                builds.append(
                    {
                        "id": build.id,
                        "status": build.status.name if build.status else None,
                        "create_time": build.create_time.isoformat()
                        if build.create_time
                        else None,
                        "source": build.source.repo_source.commit_sha
                        if build.source and build.source.repo_source
                        else None,
                        "logs_url": build.logs_url,
                    }
                )

            return json.dumps(
                {"status": "success", "builds": builds, "count": len(builds)}, indent=2
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def create_build_trigger(
        trigger_config: Dict,
        project_id: str = None,
    ) -> str:
        """
        Create a new Cloud Build trigger

        Args:
            trigger_config: Dictionary containing the trigger configuration
            project_id: GCP project ID (defaults to configured project)
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().cloudbuild
            project_id = project_id or client_instances.get_project_id()

            # Convert config dict to Trigger object
            trigger = cloudbuild_v1.BuildTrigger.from_json(json.dumps(trigger_config))

            print(f"Creating trigger in project {project_id}...")
            response = client.create_trigger(project_id=project_id, trigger=trigger)

            return json.dumps(
                {
                    "status": "success",
                    "trigger_id": response.id,
                    "name": response.name,
                    "description": response.description,
                    "create_time": response.create_time.isoformat()
                    if response.create_time
                    else None,
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    # Prompts
    @mcp_instance.prompt()
    def build_config_prompt(service_type: str = "docker") -> str:
        """Prompt for creating a Cloud Build configuration"""
        return f"""
I need to create a Cloud Build configuration for {service_type} deployments. Please help with:

1. Recommended build steps for {service_type}
2. Proper use of substitutions
3. Caching strategies
4. Security best practices
5. Integration with other GCP services
"""

    @mcp_instance.prompt()
    def trigger_setup_prompt(repo_type: str = "github") -> str:
        """Prompt for configuring build triggers"""
        return f"""
I want to set up a {repo_type} trigger for Cloud Build. Please explain:

1. Required permissions and connections
2. Event types (push, PR, etc.)
3. File pattern matching
4. Branch/tag filtering
5. Approval workflows
"""
