"""Common utility functions."""


def format_resource_name(project_id: str, resource_name: str) -> str:
    """Format a resource name with project ID."""
    return f"projects/{project_id}/resources/{resource_name}"
