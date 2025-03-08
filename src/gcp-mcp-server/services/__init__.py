"""
GCP MCP Server services package.
This package contains service modules that register tools and resources with the MCP server.
"""

# The following allows these modules to be imported directly from the services package
from . import (
    artifact_registry,
    client_instances,
    cloud_audit_logs,
    cloud_bigquery,
    cloud_build,
    cloud_compute_engine,
    cloud_monitoring,
    cloud_run,
    cloud_storage,
)
