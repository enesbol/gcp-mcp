import os

# At the top of main.py, add these imports and logging statements
import sys

# Get the directory containing main.py
current_dir = os.path.dirname(os.path.abspath(__file__))
# Add it to Python's module search path
sys.path.append(current_dir)
# Also add the parent directory if needed
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)


import inspect
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict

# Import the GCP Clients and Context
from mcp.server.fastmcp import FastMCP
from services import client_instances

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# After adding paths, print them to see what's happening
print(f"Current working directory: {os.getcwd()}")
print(f"Updated Python path: {sys.path}")


@asynccontextmanager
async def gcp_lifespan(server) -> AsyncIterator[Dict[str, Any]]:
    """Set up GCP context with credentials."""
    logger.info("Initializing GCP MCP server...")
    try:
        # Initialize GCP credentials
        credentials = None
        # Check for service account key file path
        sa_path = os.environ.get("GCP_SERVICE_ACCOUNT_KEY_PATH")
        if sa_path and os.path.exists(sa_path):
            logger.info(f"Using service account key from: {sa_path}")

        # Initialize GCP clients using the client_instances module
        client_instances.initialize_clients(credentials)
        clients = client_instances.get_clients()
        project_id = client_instances.get_project_id()
        location = client_instances.get_location()

        logger.info(f"Server initialized with project: {project_id}")
        # Yield context with clients and credentials
        yield {
            "clients": clients,
            "project_id": project_id,
            "credentials": credentials,
            "location": location,
        }
    except Exception as e:
        logger.error(f"Failed to initialize GCP context: {str(e)}")
        raise
    finally:
        logger.info("Shutting down GCP MCP server...")


# Create the global MCP instance
mcp = FastMCP(
    "GCP Manager",
    description="Manage Google Cloud Platform Resources",
    lifespan=gcp_lifespan,
    dependencies=[
        "mcp>=1.0.0",
        "google-cloud-bigquery",
        "google-cloud-storage",
        "google-cloud-run",
        "google-cloud-artifact-registry",
        "google-cloud-logging",
        "python-dotenv",
        "google-cloud-monitoring",
        "google-cloud-compute",
        "google-cloud-build",
    ],
)


# Basic resources and tools
@mcp.resource("test://hello")
def hello_resource():
    """A simple test resource"""
    return "Hello World"


@mcp.tool()
def test_gcp_auth() -> str:
    """Test GCP authentication"""
    try:
        # Get clients from client_instances module instead of context
        clients = client_instances.get_clients()

        # Test if we can list storage buckets
        if hasattr(clients, "storage"):
            try:
                buckets = list(clients.storage.list_buckets(max_results=5))
                return f"Authentication successful. Found {len(buckets)} buckets. {buckets}"
            except Exception as e:
                return f"Storage authentication failed: {str(e)}"
    except Exception as e:
        return f"Authentication failed: {str(e)}"


# # Function to register services
# def register_services():
#     """Register all service modules with the MCP instance."""
#     services_dir = os.path.join(os.path.dirname(__file__), "services")
#     logger.info(f"Loading services from {services_dir}")
#     if not os.path.exists(services_dir):
#         logger.warning(f"Services directory not found: {services_dir}")
#         return
#     # Get all Python files in the services directory
#     for filename in os.listdir(services_dir):
#         if (
#             filename.endswith(".py")
#             and filename != "__init__.py"
#             and filename != "client_instances.py"
#         ):
#             module_name = filename[:-3]  # Remove .py extension
#             try:
#                 # Load the module using importlib
#                 module_path = os.path.join(services_dir, filename)
#                 spec = importlib.util.spec_from_file_location(
#                     f"services.{module_name}", module_path
#                 )
#                 module = importlib.util.module_from_spec(spec)
#                 # Inject mcp instance into the module
#                 module.mcp = mcp
#                 # Execute the module
#                 spec.loader.exec_module(module)
#                 logger.info(f"Loaded service module: {module_name}")
#                 # If the module has a register function, call it
#                 if hasattr(module, "register"):
#                     # Pass the mcp instance and the server's request_context to register
#                     module.register(mcp)
#                     logger.info(f"Registered service: {module_name}")
#             except Exception as e:
#                 logger.error(f"Error loading service {module_name}: {e}")


def register_services():
    """Register all service modules with the MCP instance."""
    logger.info("Explicitly registering service modules")

    # Print diagnostic information
    logger.info(f"Python sys.path: {sys.path}")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Script location: {os.path.abspath(__file__)}")
    logger.info(f"Parent directory: {os.path.dirname(os.path.abspath(__file__))}")

    try:
        # Try importing a service module to check if imports work
        logger.info("Attempting to import artifact_registry")
        import services.artifact_registry as artifact_registry

        logger.info(f"Module location: {inspect.getfile(artifact_registry)}")
        from services import (
            artifact_registry,
            cloud_audit_logs,
            cloud_bigquery,
            cloud_build,
            cloud_compute_engine,
            cloud_monitoring,
            cloud_run,
            cloud_storage,
        )

        # Register each service module
        artifact_registry.register(mcp)
        cloud_audit_logs.register(mcp)
        cloud_bigquery.register(mcp)
        cloud_build.register(mcp)
        cloud_compute_engine.register(mcp)
        cloud_monitoring.register(mcp)
        cloud_run.register(mcp)
        cloud_storage.register(mcp)

        logger.info("All service modules registered successfully")
    except Exception as e:
        logger.error(f"Error registering service modules: {e}")
        # Add detailed error logging
        import traceback

        logger.error(traceback.format_exc())


if __name__ == "__main__":
    logger.info("Starting GCP MCP server")
    # Register services
    register_services()
    # Run the server
    mcp.run()
