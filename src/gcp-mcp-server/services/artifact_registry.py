import json

from services import client_instances


def register(mcp_instance):
    """Register all resources and tools with the MCP instance."""

    @mcp_instance.resource(
        "gcp://artifactregistry/{project_id}/{location}/repositories"
    )
    def list_repositories_resource(project_id: str = None, location: str = None) -> str:
        """List all Artifact Registry repositories in a specific location"""
        try:
            # define the client
            client = client_instances.get_clients().artifactregistry
            project_id = project_id or client_instances.get_project_id()
            location = location or client_instances.get_location()

            # Use parameters directly from URL path
            parent = f"projects/{project_id}/locations/{location}"

            repositories = client.list_repositories(parent=parent)
            result = []
            for repo in repositories:
                result.append(
                    {
                        "name": repo.name.split("/")[-1],
                        "format": repo.format.name
                        if hasattr(repo.format, "name")
                        else str(repo.format),
                        "description": repo.description,
                        "create_time": repo.create_time.isoformat()
                        if repo.create_time
                        else None,
                        "update_time": repo.update_time.isoformat()
                        if repo.update_time
                        else None,
                        "kms_key_name": repo.kms_key_name,
                        "labels": dict(repo.labels) if repo.labels else {},
                    }
                )
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    # Add a tool for creating repositories
    @mcp_instance.tool()
    def create_artifact_repository(
        name: str, format: str, description: str = ""
    ) -> str:
        """Create a new Artifact Registry repository"""
        try:
            # define the client
            client = client_instances.get_clients().artifactregistry
            project_id = client_instances.get_project_id()
            location = client_instances.get_location()

            parent = f"projects/{project_id}/locations/{location}"

            # Create repository request
            from google.cloud.artifactregistry_v1 import (
                CreateRepositoryRequest,
                Repository,
            )

            # Create the repository format enum value
            if format.upper() not in ["DOCKER", "MAVEN", "NPM", "PYTHON", "APT", "YUM"]:
                return json.dumps(
                    {
                        "error": f"Invalid format: {format}. Must be one of: DOCKER, MAVEN, NPM, PYTHON, APT, YUM"
                    },
                    indent=2,
                )

            repo = Repository(
                name=f"{parent}/repositories/{name}",
                format=getattr(Repository.Format, format.upper()),
                description=description,
            )

            request = CreateRepositoryRequest(
                parent=parent, repository_id=name, repository=repo
            )

            operation = client.create_repository(request=request)
            result = operation.result()  # Wait for operation to complete

            return json.dumps(
                {
                    "name": result.name.split("/")[-1],
                    "format": result.format.name
                    if hasattr(result.format, "name")
                    else str(result.format),
                    "description": result.description,
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
            return json.dumps({"error": str(e)}, indent=2)


#     @mcp_instance.tool()
#     def get_artifact_repository(
#         project_id: str = None,
#         location: str = None,
#         repository_id: str = None,
#     ) -> str:
#         """Get details about a specific Artifact Registry repository"""
#         try:
#             # Get the client from the context
#             clients = ctx.lifespan_context["clients"]
#             client = clients.artifactregistry

#             # Use context values if parameters not provided
#             project_id = project_id or ctx.lifespan_context["project_id"]
#             location = location or ctx.lifespan_context["location"]

#             if not repository_id:
#                 return json.dumps({"error": "Repository ID is required"}, indent=2)

#             name = f"projects/{project_id}/locations/{location}/repositories/{repository_id}"

#             repo = client.get_repository(name=name)
#             result = {
#                 "name": repo.name.split("/")[-1],
#                 "format": repo.format.name
#                 if hasattr(repo.format, "name")
#                 else str(repo.format),
#                 "description": repo.description,
#                 "create_time": repo.create_time.isoformat()
#                 if repo.create_time
#                 else None,
#                 "update_time": repo.update_time.isoformat()
#                 if repo.update_time
#                 else None,
#                 "kms_key_name": repo.kms_key_name,
#                 "labels": dict(repo.labels) if repo.labels else {},
#             }
#             return json.dumps(result, indent=2)
#         except Exception as e:
#             return json.dumps({"error": str(e)}, indent=2)

#     @mcp_instance.tool()
#     def upload_artifact(
#         repo_name: str,
#         artifact_path: str,
#         package: str = "",
#         version: str = "",
#         project_id: str = None,
#         location: str = None,
#     ) -> str:
#         """
#         Upload an artifact to Artifact Registry

#         Args:
#             project_id: GCP project ID
#             location: GCP region (e.g., us-central1)
#             repo_name: Name of the repository
#             artifact_path: Local path to the artifact file
#             package: Package name (optional)
#             version: Version string (optional)
#         """
#         import os

#         try:
#             # Get the client from the context
#             clients = ctx.lifespan_context["clients"]
#             client = clients.artifactregistry

#             # Use context values if parameters not provided
#             project_id = project_id or ctx.lifespan_context["project_id"]
#             location = location or ctx.lifespan_context["location"]

#             if not os.path.exists(artifact_path):
#                 return json.dumps(
#                     {"status": "error", "message": f"File not found: {artifact_path}"}
#                 )

#             filename = os.path.basename(artifact_path)
#             file_size = os.path.getsize(artifact_path)

#             parent = (
#                 f"projects/{project_id}/locations/{location}/repositories/{repo_name}"
#             )

#             with open(artifact_path, "rb") as f:
#                 file_contents = f.read()
#                 # Use the standard client for upload
#                 result = client.upload_artifact(
#                     parent=parent, contents=file_contents, artifact_path=filename
#                 )

#                 return json.dumps(
#                     {
#                         "status": "success",
#                         "uri": result.uri if hasattr(result, "uri") else None,
#                         "message": f"Successfully uploaded {filename}",
#                     },
#                     indent=2,
#                 )
#         except Exception as e:
#             return json.dumps({"status": "error", "message": str(e)}, indent=2)

#     # Prompts
#     @mcp_instance.prompt()
#     def create_repository_prompt(location: str = "us-central1") -> str:
#         """Prompt for creating a new Artifact Registry repository"""
#         return f"""
#     I need to create a new Artifact Registry repository in {location}.

#     Please help me with:
#     1. What formats are available (Docker, NPM, Maven, etc.)
#     2. Best practices for naming repositories
#     3. Recommendations for labels I should apply
#     4. Steps to create the repository
#     """

#     @mcp_instance.prompt()
#     def upload_artifact_prompt(repo_format: str = "DOCKER") -> str:
#         """Prompt for help with uploading artifacts"""
#         return f"""
#     I need to upload a {repo_format.lower()} artifact to my Artifact Registry repository.

#     Please help me understand:
#     1. The recommended way to upload {repo_format.lower()} artifacts
#     2. Any naming conventions I should follow
#     3. How to ensure proper versioning
#     4. The steps to perform the upload
#     """


# import json
# import os
# from typing import Optional

# from google.cloud import artifactregistry_v1
# from mcp.server.fastmcp import Context

# # Instead of importing from core.server


# # Resources
# @mcp.resource("gcp://artifactregistry/{project_id}/{location}/repositories")
# def list_repositories_resource(
#     project_id: str = None, location: str = None, ctx: Context = None
# ) -> str:
#     """List all Artifact Registry repositories in a specific location"""
#     client = ctx.clients.artifactregistry
#     project_id = project_id or ctx.clients.project_id
#     location = location or ctx.clients.location

#     parent = f"projects/{project_id}/locations/{location}"
#     repositories = client.list_repositories(parent=parent)

#     result = []
#     for repo in repositories:
#         result.append(
#             {
#                 "name": repo.name.split("/")[-1],
#                 "format": repo.format.name,
#                 "description": repo.description,
#                 "create_time": repo.create_time.isoformat()
#                 if repo.create_time
#                 else None,
#                 "update_time": repo.update_time.isoformat()
#                 if repo.update_time
#                 else None,
#                 "kms_key_name": repo.kms_key_name,
#                 "labels": dict(repo.labels) if repo.labels else {},
#             }
#         )

#     return json.dumps(result, indent=2)


# @mcp.resource("gcp://artifactregistry/{project_id}/{location}/repository/{repo_name}")
# def get_repository_resource(
#     repo_name: str, project_id: str = None, location: str = None, ctx: Context = None
# ) -> str:
#     """Get details for a specific Artifact Registry repository"""
#     client = ctx.clients.artifactregistry
#     project_id = project_id or ctx.clients.project_id
#     location = location or ctx.clients.location

#     name = f"projects/{project_id}/locations/{location}/repositories/{repo_name}"

#     try:
#         repo = client.get_repository(name=name)
#         result = {
#             "name": repo.name.split("/")[-1],
#             "format": repo.format.name,
#             "description": repo.description,
#             "create_time": repo.create_time.isoformat() if repo.create_time else None,
#             "update_time": repo.update_time.isoformat() if repo.update_time else None,
#             "kms_key_name": repo.kms_key_name,
#             "labels": dict(repo.labels) if repo.labels else {},
#         }
#         return json.dumps(result, indent=2)
#     except Exception as e:
#         return json.dumps({"error": str(e)})


# @mcp.resource(
#     "gcp://artifactregistry/{project_id}/{location}/repository/{repo_name}/packages"
# )
# def list_packages_resource(
#     repo_name: str, project_id: str = None, location: str = None, ctx: Context = None
# ) -> str:
#     """List packages in a specific Artifact Registry repository"""
#     client = ctx.clients.artifactregistry
#     project_id = project_id or ctx.clients.project_id
#     location = location or ctx.clients.location

#     parent = f"projects/{project_id}/locations/{location}/repositories/{repo_name}"
#     packages = client.list_packages(parent=parent)

#     result = []
#     for package in packages:
#         result.append(
#             {
#                 "name": package.name.split("/")[-1],
#                 "display_name": package.display_name,
#                 "create_time": package.create_time.isoformat()
#                 if package.create_time
#                 else None,
#                 "update_time": package.update_time.isoformat()
#                 if package.update_time
#                 else None,
#             }
#         )

#     return json.dumps(result, indent=2)


# # Tools
# @mcp.tool()
# async def create_repository(
#     repo_name: str,
#     format: str = "DOCKER",
#     description: str = "",
#     labels: Optional[dict] = None,
#     project_id: str = None,
#     location: str = None,
#     ctx: Context = None,
# ) -> str:
#     """
#     Create an Artifact Registry repository

#     Args:
#         project_id: GCP project ID
#         location: GCP region (e.g., us-central1)
#         repo_name: Name for the new repository
#         format: Repository format (DOCKER, NPM, PYTHON, MAVEN, APT, YUM, GO)
#         description: Optional description for the repository
#         labels: Optional key-value pairs for repository labels
#     """
#     client = ctx.clients.artifactregistry
#     project_id = project_id or ctx.clients.project_id
#     location = location or ctx.clients.location

#     # Validate format
#     try:
#         format_enum = artifactregistry_v1.Repository.Format[format]
#     except KeyError:
#         return json.dumps(
#             {
#                 "status": "error",
#                 "message": f"Invalid format: {format}. Valid formats are: {', '.join(artifactregistry_v1.Repository.Format._member_names_)}",
#             }
#         )

#     # Create repository
#     parent = f"projects/{project_id}/locations/{location}"
#     repository = artifactregistry_v1.Repository(
#         format=format_enum,
#         description=description,
#     )

#     if labels:
#         repository.labels = labels

#     request = artifactregistry_v1.CreateRepositoryRequest(
#         parent=parent, repository_id=repo_name, repository=repository
#     )

#     try:
#         ctx.info(f"Creating repository {repo_name} in {location}...")
#         response = client.create_repository(request=request)

#         return json.dumps(
#             {
#                 "status": "success",
#                 "name": response.name,
#                 "format": response.format.name,
#                 "description": response.description,
#                 "create_time": response.create_time.isoformat()
#                 if response.create_time
#                 else None,
#             },
#             indent=2,
#         )
#     except Exception as e:
#         return json.dumps({"status": "error", "message": str(e)})


# @mcp.tool()
# async def list_repositories(
#     project_id: str = None, location: str = None, ctx: Context = None
# ) -> str:
#     """
#     List Artifact Registry repositories in a specific location

#     Args:
#         project_id: GCP project ID
#         location: GCP region (e.g., us-central1)
#     """
#     client = ctx.clients.artifactregistry
#     project_id = project_id or ctx.clients.project_id
#     location = location or ctx.clients.location

#     parent = f"projects/{project_id}/locations/{location}"

#     try:
#         ctx.info(f"Listing repositories in {location}...")
#         repositories = client.list_repositories(parent=parent)

#         result = []
#         for repo in repositories:
#             result.append(
#                 {
#                     "name": repo.name.split("/")[-1],
#                     "format": repo.format.name,
#                     "description": repo.description,
#                     "create_time": repo.create_time.isoformat()
#                     if repo.create_time
#                     else None,
#                 }
#             )

#         return json.dumps(
#             {"status": "success", "repositories": result, "count": len(result)},
#             indent=2,
#         )
#     except Exception as e:
#         return json.dumps({"status": "error", "message": str(e)})
