import importlib.util
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict

# Import the GCP Clients and Context
from mcp.server.fastmcp import FastMCP
from services import client_instances

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


# Function to register services
def register_services():
    """Register all service modules with the MCP instance."""
    services_dir = os.path.join(os.path.dirname(__file__), "services")
    logger.info(f"Loading services from {services_dir}")
    if not os.path.exists(services_dir):
        logger.warning(f"Services directory not found: {services_dir}")
        return
    # Get all Python files in the services directory
    for filename in os.listdir(services_dir):
        if (
            filename.endswith(".py")
            and filename != "__init__.py"
            and filename != "client_instances.py"
        ):
            module_name = filename[:-3]  # Remove .py extension
            try:
                # Load the module using importlib
                module_path = os.path.join(services_dir, filename)
                spec = importlib.util.spec_from_file_location(
                    f"services.{module_name}", module_path
                )
                module = importlib.util.module_from_spec(spec)
                # Inject mcp instance into the module
                module.mcp = mcp
                # Execute the module
                spec.loader.exec_module(module)
                logger.info(f"Loaded service module: {module_name}")
                # If the module has a register function, call it
                if hasattr(module, "register"):
                    # Pass the mcp instance and the server's request_context to register
                    module.register(mcp)
                    logger.info(f"Registered service: {module_name}")
            except Exception as e:
                logger.error(f"Error loading service {module_name}: {e}")


if __name__ == "__main__":
    logger.info("Starting GCP MCP server")
    # Register services
    register_services()
    # Run the server
    mcp.run()
