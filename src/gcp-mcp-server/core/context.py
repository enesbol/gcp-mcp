# context.py
import json
import os
from typing import Any, Optional, Type

import google.auth
from google.cloud import artifactregistry_v1, storage

# Import other services as needed
# from google.cloud import bigquery, compute_v1, logging_v2, monitoring_v3, run_v2, storage
from google.oauth2 import service_account


class GCPClients:
    """Client manager for GCP services"""

    def __init__(self, credentials=None):
        self.credentials = self._get_credentials(credentials)
        self.project_id = self._get_project_id()
        self.location = self._get_location()
        self._clients = {}

        # Initialize clients
        self._storage_client = None
        self._bigquery_client = None
        self._run_client = None
        self._logging_client = None
        self._monitoring_client = None
        self._compute_client = None
        self._sql_client = None
        self._cloudbuild_client = None
        self._artifactregistry_client = None

    def _get_credentials(self, credentials=None):
        """Get credentials from various sources"""
        # If credentials are directly provided
        if credentials:
            return credentials

        # Check for service account JSON in environment variable
        sa_json = os.environ.get("GCP_SERVICE_ACCOUNT_JSON")
        if sa_json:
            try:
                sa_info = json.loads(sa_json)
                return service_account.Credentials.from_service_account_info(sa_info)
            except Exception as e:
                print(f"Error loading service account JSON: {e}")

        # Check for service account key file path
        sa_path = os.environ.get("GCP_SERVICE_ACCOUNT_KEY_PATH")
        if sa_path:
            try:
                return service_account.Credentials.from_service_account_file(sa_path)
            except Exception as e:
                print(f"Error loading service account key file: {e}")

        # Fall back to application default credentials
        try:
            credentials, project = google.auth.default()
            return credentials
        except Exception as e:
            print(f"Error getting default credentials: {e}")
            raise RuntimeError("No valid GCP credentials found")

    def _get_project_id(self) -> str:
        """Get project ID from environment or credentials"""
        project_id = os.environ.get("GCP_PROJECT_ID")
        if project_id:
            return project_id

        if hasattr(self.credentials, "project_id"):
            return self.credentials.project_id

        try:
            _, project_id = google.auth.default()
            return project_id
        except Exception:
            raise RuntimeError("Unable to determine GCP project ID")

    def _get_location(self) -> str:
        """Get default location/region from environment"""
        return os.environ.get("GCP_LOCATION", "us-central1")

    # def _init_client(
    #     self, client_class: Type, current_client: Optional[Any], **kwargs
    # ) -> Any:
    #     """Helper method to initialize clients with error handling"""
    #     if not current_client:
    #         try:
    #             return client_class(
    #                 project=self.project_id,  # <-- This adds project automatically
    #                 credentials=self.credentials,  # <-- This adds credentials automatically
    #                 **kwargs,  # <-- This adds any extra params (like database)
    #             )
    #         except Exception as e:
    #             raise RuntimeError(
    #                 f"Failed to initialize {client_class.__name__}: {str(e)}"
    #             )
    #     return current_client

    def _init_client(
        self, client_class: Type, current_client: Optional[Any], **kwargs
    ) -> Any:
        """Helper method to initialize clients with error handling"""
        if not current_client:
            try:
                # Check if this client accepts project parameter
                if client_class in [
                    storage.Client
                ]:  # Add other clients that accept project
                    kwargs["project"] = self.project_id

                return client_class(credentials=self.credentials, **kwargs)
            except Exception as e:
                raise RuntimeError(
                    f"Failed to initialize {client_class.__name__}: {str(e)}"
                )
        return current_client

    @property
    def storage(self) -> storage.Client:
        self._storage_client = self._init_client(storage.Client, self._storage_client)
        return self._storage_client

    @property
    def artifactregistry(self) -> artifactregistry_v1.ArtifactRegistryClient:
        """Get the Artifact Registry client."""
        if not self._artifactregistry_client:
            try:
                # ArtifactRegistryClient doesn't accept project parameter
                self._artifactregistry_client = (
                    artifactregistry_v1.ArtifactRegistryClient(
                        credentials=self.credentials
                    )
                )
            except Exception as e:
                raise RuntimeError(
                    f"Failed to initialize ArtifactRegistryClient: {str(e)}"
                )
        return self._artifactregistry_client

    # Uncomment and implement other client properties as needed
    # @property
    # def storage(self) -> storage.Client:
    #     self._storage_client = self._init_client(storage.Client, self._storage_client)
    #     return self._storage_client

    def close_all(self):
        """Close all open clients"""
        for client in self._clients.values():
            if hasattr(client, "transport") and hasattr(client.transport, "close"):
                client.transport.close()
            elif hasattr(client, "close"):
                client.close()
        self._clients.clear()


# Update Context class to handle credentials properly
class Context:
    def __init__(self, request_context):
        self.request_context = request_context
        # Get credentials from lifespan context
        credentials = request_context.lifespan_context.get("credentials")
        # Initialize GCPClients with those credentials
        self.clients = GCPClients(credentials)

    def close(self):
        """Clean up when request ends"""
        if hasattr(self, "clients"):
            self.clients.close_all()

    @property
    def storage(self) -> storage.Client:
        self._storage_client = self._init_client(storage.Client, self._storage_client)
        return self._storage_client

    # @property
    # def bigquery(self) -> bigquery.Client:
    #     self._bigquery_client = self._init_client(
    #         bigquery.Client, self._bigquery_client
    #     )
    #     return self._bigquery_client

    # @property
    # def run(self) -> run_v2.CloudRunClient:
    #     self._run_client = self._init_client(run_v2.CloudRunClient, self._run_client)
    #     return self._run_client

    # @property
    # def logging(self) -> logging_v2.LoggingServiceV2Client:
    #     self._logging_client = self._init_client(
    #         logging_v2.LoggingServiceV2Client, self._logging_client
    #     )
    #     return self._logging_client

    # @property
    # def monitoring(self) -> monitoring_v3.MetricServiceClient:
    #     self._monitoring_client = self._init_client(
    #         monitoring_v3.MetricServiceClient, self._monitoring_client
    #     )
    #     return self._monitoring_client

    # @property
    # def compute(self) -> compute_v1.InstancesClient:
    #     self._compute_client = self._init_client(
    #         compute_v1.InstancesClient, self._compute_client
    #     )
    #     return self._compute_client

    # @property
    # def sql(self) -> sql_v1.InstancesClient:
    #     self._sql_client = self._init_client(sql_v1.InstancesClient, self._sql_client)
    #     return self._sql_client

    # @property
    # def cloudbuild(self) -> cloudbuild_v1.CloudBuildClient:
    #     self._cloudbuild_client = self._init_client(
    #         cloudbuild_v1.CloudBuildClient, self._cloudbuild_client
    #     )
    #     return self._cloudbuild_client
