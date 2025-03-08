import logging

from core.context import GCPClients

# Set up logging
logger = logging.getLogger(__name__)

# Global client instance
_gcp_clients = None
_project_id = None
_location = None


def initialize_clients(credentials=None):
    """Initialize GCP clients with credentials."""
    global _gcp_clients, _project_id, _location

    try:
        # Initialize GCP clients
        _gcp_clients = GCPClients(credentials)
        _project_id = _gcp_clients.project_id
        _location = _gcp_clients.location
        logger.info(f"GCP clients initialized with project: {_project_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize GCP clients: {str(e)}")
        return False


def get_clients():
    """Get the initialized GCP clients."""
    if _gcp_clients is None:
        logger.warning("GCP clients not initialized. Attempting to initialize...")
        initialize_clients()
    return _gcp_clients


def get_project_id():
    """Get the GCP project ID."""
    return _project_id


def get_location():
    """Get the GCP location."""
    return _location
