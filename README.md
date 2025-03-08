# This is not a Ready MCP Server



# GCP MCP Server

A comprehensive Model Context Protocol (MCP) server implementation for Google Cloud Platform (GCP) services, enabling AI assistants to interact with and manage GCP resources through a standardized interface.

## Overview

GCP MCP Server provides AI assistants with capabilities to:

- **Query GCP Resources**: Get information about your cloud infrastructure
- **Manage Cloud Resources**: Create, configure, and manage GCP services
- **Receive Assistance**: Get AI-guided help with GCP configurations and best practices

The implementation follows the MCP specification to enable AI systems to interact with GCP services in a secure, controlled manner.

## Supported GCP Services

This implementation includes support for the following GCP services:

- **Artifact Registry**: Container and package management
- **BigQuery**: Data warehousing and analytics
- **Cloud Audit Logs**: Logging and audit trail analysis
- **Cloud Build**: CI/CD pipeline management
- **Cloud Compute Engine**: Virtual machine instances
- **Cloud Monitoring**: Metrics, alerting, and dashboards
- **Cloud Run**: Serverless container deployments
- **Cloud Storage**: Object storage management

## Architecture

The project is structured as follows:

```
gcp-mcp-server/
├── core/            # Core MCP server functionality auth context logging_handler security 
├── prompts/         # AI assistant prompts for GCP operations
├── services/        # GCP service implementations
│   ├── README.md    # Service implementation details
│   └── ...          # Individual service modules
├── main.py          # Main server entry point
└── ...
```

Key components:

- **Service Modules**: Each GCP service has its own module with resources, tools, and prompts
- **Client Instances**: Centralized client management for authentication and resource access
- **Core Components**: Base functionality for the MCP server implementation

## Getting Started

### Prerequisites

- Python 3.10+
- GCP project with enabled APIs for the services you want to use
- Authenticated GCP credentials (Application Default Credentials recommended)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/gcp-mcp-server.git
   cd gcp-mcp-server
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure your GCP credentials:
   ```bash
   # Using gcloud
   gcloud auth application-default login
   
   # Or set GOOGLE_APPLICATION_CREDENTIALS
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
   ```

5. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Running the Server

Start the MCP server:

```bash
python main.py
```

For development and testing:

```bash
# Development mode with auto-reload
python main.py --dev

# Run with specific configuration
python main.py --config config.yaml
```

## Docker Deployment

Build and run with Docker:

```bash
# Build the image
docker build -t gcp-mcp-server .

# Run the container
docker run -p 8080:8080 -v ~/.config/gcloud:/root/.config/gcloud gcp-mcp-server
```

## Configuration

The server can be configured through environment variables or a configuration file:

| Environment Variable | Description | Default |
|----------------------|-------------|---------|
| `GCP_PROJECT_ID` | Default GCP project ID | None (required) |
| `GCP_DEFAULT_LOCATION` | Default region/zone | `us-central1` |
| `MCP_SERVER_PORT` | Server port | `8080` |
| `LOG_LEVEL` | Logging level | `INFO` |

See `.env.example` for a complete list of configuration options.
 
## Development

### Adding a New GCP Service

1. Create a new file in the `services/` directory
2. Implement the service following the pattern in existing services
3. Register the service in `main.py`

See the [services README](services/README.md) for detailed implementation guidance.
 

## Security Considerations

- The server uses Application Default Credentials for authentication
- Authorization is determined by the permissions of the authenticated identity
- No credentials are hardcoded in the service implementations
- Consider running with a service account with appropriate permissions

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Google Cloud Platform team for their comprehensive APIs
- Model Context Protocol for providing a standardized way for AI to interact with services

### Using the Server

To use this server:

1. Place your GCP service account key file as `service-account.json` in the same directory
2. Install the MCP package: `pip install "mcp[cli]"`
3. Install the required GCP package: `pip install google-cloud-run`
4. Run: `mcp dev gcp_cloudrun_server.py`

Or install it in Claude Desktop:
```
mcp install gcp_cloudrun_server.py --name "GCP Cloud Run Manager"
```


## MCP Server Configuration

The following configuration can be added to your configuration file for GCP Cloud Tools:

```json
"mcpServers": {
  "GCP Cloud Tools": {
    "command": "uv",
    "args": [
      "run",
      "--with",
      "google-cloud-artifact-registry>=1.10.0",
      "--with",
      "google-cloud-bigquery>=3.27.0",
      "--with",
      "google-cloud-build>=3.0.0",
      "--with",
      "google-cloud-compute>=1.0.0",
      "--with",
      "google-cloud-logging>=3.5.0",
      "--with",
      "google-cloud-monitoring>=2.0.0",
      "--with",
      "google-cloud-run>=0.9.0",
      "--with",
      "google-cloud-storage>=2.10.0",
      "--with",
      "mcp[cli]",
      "--with",
      "python-dotenv>=1.0.0",
      "mcp",
      "run",
      "C:\\Users\\enes_\\Desktop\\mcp-repo-final\\gcp-mcp\\src\\gcp-mcp-server\\main.py"
    ],
    "env": {
      "GOOGLE_APPLICATION_CREDENTIALS": "C:/Users/enes_/Desktop/mcp-repo-final/gcp-mcp/service-account.json",
      "GCP_PROJECT_ID": "gcp-mcp-cloud-project",
      "GCP_LOCATION": "us-east1"
    }
  }
}
```

### Configuration Details

This configuration sets up an MCP server for Google Cloud Platform tools with the following:

- **Command**: Uses `uv` package manager to run the server
- **Dependencies**: Includes various Google Cloud libraries (Artifact Registry, BigQuery, Cloud Build, etc.)
- **Environment Variables**:
  - `GOOGLE_APPLICATION_CREDENTIALS`: Path to your GCP service account credentials
  - `GCP_PROJECT_ID`: Your Google Cloud project ID
  - `GCP_LOCATION`: GCP region (us-east1)

### Usage

Add this configuration to your MCP configuration file to enable GCP Cloud Tools functionality.
