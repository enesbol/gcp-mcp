"""Common prompts for GCP operations."""

from ..core import mcp


@mcp.prompt()
def gcp_service_help(service_name: str) -> str:
    """Get help for using a GCP service."""
    return f"""
    I need help with using {service_name} in Google Cloud Platform.
    
    Please help me understand:
    1. Common operations and best practices
    2. Required parameters and configuration
    3. Security considerations
    4. Recommended patterns for {service_name}
    """


@mcp.prompt()
def error_analysis(error_message: str) -> str:
    """Analyze a GCP error message."""
    return f"""
    I received this error from GCP:
    {error_message}
    
    Please help me:
    1. Understand what caused this error
    2. Find potential solutions
    3. Prevent similar errors in the future
    """
