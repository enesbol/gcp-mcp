# GCP Services MCP Implementation

This repository contains Model Context Protocol (MCP) implementations for various Google Cloud Platform (GCP) services. These modules expose GCP resources, tools, and prompts in a standardized way for AI assistants to interact with GCP infrastructure.

## Overview

The MCP framework provides a consistent way to expose cloud resources to AI assistants. Each service module follows a common pattern:

1. A `register` function that takes an MCP instance as a parameter
2. Resources for retrieving information about GCP resources
3. Tools for performing operations on GCP resources
4. Prompts for guiding users through common tasks

## Implementation Pattern

All service modules follow a consistent implementation pattern:

```python
import json
from services import client_instances
from google.cloud import service_client

def register(mcp_instance):
    """Register all resources and tools with the MCP instance."""
    
    # Resources
    @mcp_instance.resource("gcp://service/{project_id}/resources")
    def list_resources(project_id: str = None) -> str:
        # Implement resource listing
        pass
        
    # Tools
    @mcp_instance.tool()
    def create_resource(resource_name: str, project_id: str = None) -> str:
        # Implement resource creation
        pass
        
    # Prompts
    @mcp_instance.prompt()
    def configuration_help() -> str:
        # Return helpful prompt text
        return """Help text here"""
```

## Key Design Principles

### 1. Client Management

Clients are accessed through a central `client_instances` module:

```python
client = client_instances.get_clients().service_name
```

This approach:
- Centralizes client creation and authentication
- Avoids duplicating client instantiation logic
- Enables consistent credential management

### 2. Parameter Defaults

Required parameters come first, followed by optional parameters with sensible defaults:

```python
def create_resource(
    resource_name: str,     # Required parameter first
    project_id: str = None, # Optional parameters with defaults
    location: str = None
) -> str:
    # Use defaults from client_instances when not provided
    project_id = project_id or client_instances.get_project_id()
    location = location or client_instances.get_location()
```

### 3. Error Handling

All functions include consistent error handling:

```python
try:
    # Implementation code
    return json.dumps(result, indent=2)
except Exception as e:
    return json.dumps({"error": str(e)}, indent=2)
```

### 4. JSON Responses

All responses are consistently formatted JSON strings with proper indentation:

```python
return json.dumps(
    {
        "status": "success",
        "resources": result,
        "count": len(result)
    },
    indent=2
)
```

### 5. Defensive Coding

All implementations use defensive coding practices to handle potentially missing or null values:

```python
"labels": dict(resource.labels) if resource.labels else {}
```

## Available Services

The following GCP services are implemented:

1. **BigQuery** - Data warehouse operations
2. **Cloud Storage** - Object storage operations 
3. **Cloud Run** - Serverless container management
4. **Cloud Build** - CI/CD pipeline management
5. **Artifact Registry** - Container and package registry
6. **Compute Engine** - VM instance management
7. **Cloud Monitoring** - Metrics and alerting
8. **Cloud Audit Logs** - Logging and auditing

## Service-Specific Features

### BigQuery

- Dataset and table management
- Query execution
- Data import/export

### Cloud Storage

- Bucket management
- Object operations (upload, download, delete)
- Bucket configuration

### Cloud Run

- Service deployment
- Service configuration
- Traffic management

### Cloud Build

- Trigger management
- Build execution
- Build monitoring

### Artifact Registry

- Repository management
- Package operations

### Compute Engine

- Instance lifecycle management
- Instance configuration

### Cloud Monitoring

- Metric exploration
- Alert policy management
- Notification channel configuration

### Cloud Audit Logs

- Log querying
- Log sink management

## Usage Example

To register all services with an MCP instance:

```python
from mcp.server.fastmcp import FastMCP
from services import (
    bigquery,
    storage,
    cloudrun,
    cloudbuild,
    artifactregistry,
    compute,
    monitoring,
    auditlogs
)

# Create MCP instance
mcp = FastMCP("GCP Services")

# Register all services
bigquery.register(mcp)
storage.register(mcp)
cloudrun.register(mcp)
cloudbuild.register(mcp)
artifactregistry.register(mcp)
compute.register(mcp)
monitoring.register(mcp)
auditlogs.register(mcp)
```

## Important Notes

1. **Default Project and Location**:
   - Services default to the project and location configured in `client_instances`
   - Always allow these to be overridden by parameters

2. **Authentication**:
   - Authentication is handled by the `client_instances` module
   - No credentials should be hardcoded in service implementations

3. **Error Handling**:
   - All operations should include robust error handling
   - Error responses should be informative but not expose sensitive information

4. **Response Formatting**:
   - All responses should be valid JSON with proper indentation
   - Success responses should include a "status": "success" field
   - Error responses should include a "status": "error" field with a "message"

## Best Practices for MCP Integration

1. **Resource Naming**:
   - Use consistent URI patterns for resources (gcp://service/{project_id}/resource)
   - Group related resources logically

2. **Tool Design**:
   - Design tools around specific user intents
   - Order parameters with required ones first, followed by optional ones
   - Provide sensible defaults for optional parameters

3. **Prompt Design**:
   - Create prompts for common user scenarios
   - Include enough context for the AI to provide helpful responses
   - Structure prompts as guiding questions or templates

4. **Documentation**:
   - Include descriptive docstrings for all resources, tools, and prompts
   - Document all parameters and return values
   - Include usage examples where appropriate

## Extending the Services

To add a new GCP service:

1. Create a new module following the pattern above
2. Implement resources for retrieving information
3. Implement tools for operations
4. Create prompts for common user tasks
5. Register the new service in your MCP initialization

## Troubleshooting

If you encounter issues:

1. Check client initialization in `client_instances`
2. Verify required permissions for the service operations
3. Look for additional error details in the returned JSON
4. Add print statements for debugging complex operations