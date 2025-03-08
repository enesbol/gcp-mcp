# import logging
# import os
# from contextlib import asynccontextmanager
# from typing import Any, AsyncIterator, Dict

# from auth import get_credentials
# from mcp.server.fastmcp import FastMCP

# from ..services import bigquery, compute, iam, storage

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


# @asynccontextmanager
# async def gcp_lifespan(server) -> AsyncIterator[Dict[str, Any]]:
#     """Set up GCP context with credentials."""
#     logger.info("Initializing GCP MCP server...")
#     try:
#         # Get GCP credentials
#         credentials = get_credentials()
#         project_id = os.environ.get("GCP_PROJECT_ID")

#         if not project_id:
#             logger.warning(
#                 "GCP_PROJECT_ID not set in environment. Some features may not work correctly."
#             )

#         logger.info(f"Server initialized with project: {project_id or 'Not set'}")

#         # Yield context to be used by handlers
#         yield {"credentials": credentials, "project_id": project_id}
#     except Exception as e:
#         logger.error(f"Failed to initialize GCP context: {str(e)}")
#         raise
#     finally:
#         logger.info("Shutting down GCP MCP server...")


# # Create main server FIRST
# mcp = FastMCP(
#     "GCP Manager",
#     description="Manage Google Cloud Platform Resources",
#     lifespan=gcp_lifespan,
# )

# # Register all services
# compute.register(mcp)
# storage.register(mcp)
# bigquery.register(mcp)
# iam.register(mcp)


# # THEN define resources and tools
# @mcp.resource("gcp://project")
# def get_project_info():
#     """Get information about the current GCP project"""
#     project_id = os.environ.get("GCP_PROJECT_ID")
#     return f"Project ID: {project_id}"


# @mcp.resource("gcp://storage/buckets")
# def list_buckets():
#     """List GCP storage buckets"""
#     from google.cloud import storage

#     client = storage.Client()
#     buckets = list(client.list_buckets(max_results=10))
#     return "\n".join([f"- {bucket.name}" for bucket in buckets])


# @mcp.resource("test://hello")
# def hello_resource():
#     """A simple test resource"""
#     return "Hello World"


# @mcp.tool()
# def list_gcp_instances(region: str = "us-central1") -> str:
#     """List GCP compute instances in a region"""
#     # Use your credentials to list instances
#     return f"Instances in {region}: [instance list would go here]"


# @mcp.tool()
# def test_gcp_auth() -> str:
#     """Test GCP authentication"""
#     try:
#         from google.cloud import storage

#         client = storage.Client()
#         buckets = list(client.list_buckets(max_results=5))
#         return f"Authentication successful. Found {len(buckets)} buckets."
#     except Exception as e:
#         return f"Authentication failed: {str(e)}"


# if __name__ == "__main__":
#     mcp.run()
