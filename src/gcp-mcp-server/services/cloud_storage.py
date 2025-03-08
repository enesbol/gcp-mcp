import json
import os
from typing import Dict, Optional

from services import client_instances


def register(mcp_instance):
    """Register all Cloud Storage resources and tools with the MCP instance."""

    # Resources
    @mcp_instance.resource("gcp://storage/{project_id}/buckets")
    def list_buckets_resource(project_id: str = None) -> str:
        """List all Cloud Storage buckets in a project"""
        try:
            # Get client from client_instances
            client = client_instances.get_clients().storage
            project_id = project_id or client_instances.get_project_id()

            buckets = client.list_buckets()

            result = []
            for bucket in buckets:
                result.append(
                    {
                        "name": bucket.name,
                        "location": bucket.location,
                        "storage_class": bucket.storage_class,
                        "time_created": bucket.time_created.isoformat()
                        if bucket.time_created
                        else None,
                        "versioning_enabled": bucket.versioning_enabled,
                        "labels": dict(bucket.labels) if bucket.labels else {},
                    }
                )

            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    @mcp_instance.resource("gcp://storage/{project_id}/bucket/{bucket_name}")
    def get_bucket_resource(project_id: str = None, bucket_name: str = None) -> str:
        """Get details for a specific Cloud Storage bucket"""
        try:
            # Get client from client_instances
            client = client_instances.get_clients().storage
            project_id = project_id or client_instances.get_project_id()

            bucket = client.get_bucket(bucket_name)
            result = {
                "name": bucket.name,
                "location": bucket.location,
                "storage_class": bucket.storage_class,
                "time_created": bucket.time_created.isoformat()
                if bucket.time_created
                else None,
                "versioning_enabled": bucket.versioning_enabled,
                "requester_pays": bucket.requester_pays,
                "lifecycle_rules": bucket.lifecycle_rules,
                "cors": bucket.cors,
                "labels": dict(bucket.labels) if bucket.labels else {},
            }
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    @mcp_instance.resource("gcp://storage/{project_id}/bucket/{bucket_name}/objects")
    def list_objects_resource(
        project_id: str = None, bucket_name: str = None, prefix: str = ""
    ) -> str:
        """List objects in a specific Cloud Storage bucket"""
        try:
            # Get client from client_instances
            client = client_instances.get_clients().storage
            project_id = project_id or client_instances.get_project_id()

            bucket = client.get_bucket(bucket_name)
            blobs = bucket.list_blobs(prefix=prefix)

            result = []
            for blob in blobs:
                result.append(
                    {
                        "name": blob.name,
                        "size": blob.size,
                        "updated": blob.updated.isoformat() if blob.updated else None,
                        "content_type": blob.content_type,
                        "md5_hash": blob.md5_hash,
                        "generation": blob.generation,
                        "metadata": blob.metadata,
                    }
                )

            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    # Tools
    @mcp_instance.tool()
    def create_bucket(
        bucket_name: str,
        project_id: str = None,
        location: str = "us-central1",
        storage_class: str = "STANDARD",
        labels: Optional[Dict[str, str]] = None,
        versioning_enabled: bool = False,
    ) -> str:
        """
        Create a Cloud Storage bucket

        Args:
            bucket_name: Name for the new bucket
            project_id: GCP project ID (defaults to configured project)
            location: GCP region (e.g., us-central1)
            storage_class: Storage class (STANDARD, NEARLINE, COLDLINE, ARCHIVE)
            labels: Optional key-value pairs for bucket labels
            versioning_enabled: Whether to enable object versioning
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().storage
            project_id = project_id or client_instances.get_project_id()

            # Validate storage class
            valid_storage_classes = ["STANDARD", "NEARLINE", "COLDLINE", "ARCHIVE"]
            if storage_class not in valid_storage_classes:
                return json.dumps(
                    {
                        "status": "error",
                        "message": f"Invalid storage class: {storage_class}. Valid classes are: {', '.join(valid_storage_classes)}",
                    },
                    indent=2,
                )

            # Log info (similar to ctx.info)
            print(f"Creating bucket {bucket_name} in {location}...")
            bucket = client.bucket(bucket_name)
            bucket.create(location=location, storage_class=storage_class, labels=labels)

            # Set versioning if enabled
            if versioning_enabled:
                bucket.versioning_enabled = True
                bucket.patch()

            return json.dumps(
                {
                    "status": "success",
                    "name": bucket.name,
                    "location": bucket.location,
                    "storage_class": bucket.storage_class,
                    "time_created": bucket.time_created.isoformat()
                    if bucket.time_created
                    else None,
                    "versioning_enabled": bucket.versioning_enabled,
                    "url": f"gs://{bucket_name}/",
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def list_buckets(project_id: str = None, prefix: str = "") -> str:
        """
        List Cloud Storage buckets in a project

        Args:
            project_id: GCP project ID (defaults to configured project)
            prefix: Optional prefix to filter bucket names
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().storage
            project_id = project_id or client_instances.get_project_id()

            # Log info (similar to ctx.info)
            print(f"Listing buckets in project {project_id}...")

            # List buckets with optional prefix filter
            if prefix:
                buckets = [
                    b for b in client.list_buckets() if b.name.startswith(prefix)
                ]
            else:
                buckets = list(client.list_buckets())

            result = []
            for bucket in buckets:
                result.append(
                    {
                        "name": bucket.name,
                        "location": bucket.location,
                        "storage_class": bucket.storage_class,
                        "time_created": bucket.time_created.isoformat()
                        if bucket.time_created
                        else None,
                    }
                )

            return json.dumps(
                {"status": "success", "buckets": result, "count": len(result)}, indent=2
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def upload_object(
        bucket_name: str,
        source_file_path: str,
        destination_blob_name: Optional[str] = None,
        project_id: str = None,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Upload an object to a Cloud Storage bucket

        Args:
            bucket_name: Name of the bucket
            source_file_path: Local path to the file to upload
            destination_blob_name: Name to assign to the blob (defaults to file basename)
            project_id: GCP project ID (defaults to configured project)
            content_type: Content type of the object (optional)
            metadata: Custom metadata dictionary (optional)
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().storage
            project_id = project_id or client_instances.get_project_id()

            # Check if file exists
            if not os.path.exists(source_file_path):
                return json.dumps(
                    {
                        "status": "error",
                        "message": f"File not found: {source_file_path}",
                    },
                    indent=2,
                )

            # Get bucket
            bucket = client.bucket(bucket_name)

            # Use filename if destination_blob_name not provided
            if not destination_blob_name:
                destination_blob_name = os.path.basename(source_file_path)

            # Create blob
            blob = bucket.blob(destination_blob_name)

            # Set content type if provided
            if content_type:
                blob.content_type = content_type

            # Set metadata if provided
            if metadata:
                blob.metadata = metadata

            # Get file size for progress reporting
            file_size = os.path.getsize(source_file_path)
            print(
                f"Uploading {source_file_path} ({file_size} bytes) to gs://{bucket_name}/{destination_blob_name}..."
            )

            # Upload file
            blob.upload_from_filename(source_file_path)

            return json.dumps(
                {
                    "status": "success",
                    "bucket": bucket_name,
                    "name": blob.name,
                    "size": blob.size,
                    "content_type": blob.content_type,
                    "md5_hash": blob.md5_hash,
                    "generation": blob.generation,
                    "public_url": blob.public_url,
                    "gsutil_uri": f"gs://{bucket_name}/{destination_blob_name}",
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def download_object(
        bucket_name: str,
        source_blob_name: str,
        destination_file_path: str,
        project_id: str = None,
    ) -> str:
        """
        Download an object from a Cloud Storage bucket

        Args:
            bucket_name: Name of the bucket
            source_blob_name: Name of the blob to download
            destination_file_path: Local path where the file should be saved
            project_id: GCP project ID (defaults to configured project)
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().storage
            project_id = project_id or client_instances.get_project_id()

            # Get bucket and blob
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(source_blob_name)

            # Check if blob exists
            if not blob.exists():
                return json.dumps(
                    {
                        "status": "error",
                        "message": f"Object not found: gs://{bucket_name}/{source_blob_name}",
                    },
                    indent=2,
                )

            # Create directory if doesn't exist
            os.makedirs(
                os.path.dirname(os.path.abspath(destination_file_path)), exist_ok=True
            )

            print(
                f"Downloading gs://{bucket_name}/{source_blob_name} to {destination_file_path}..."
            )

            # Download file
            blob.download_to_filename(destination_file_path)

            return json.dumps(
                {
                    "status": "success",
                    "bucket": bucket_name,
                    "blob_name": source_blob_name,
                    "size": blob.size,
                    "content_type": blob.content_type,
                    "downloaded_to": destination_file_path,
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def delete_object(bucket_name: str, blob_name: str, project_id: str = None) -> str:
        """
        Delete an object from a Cloud Storage bucket

        Args:
            bucket_name: Name of the bucket
            blob_name: Name of the blob to delete
            project_id: GCP project ID (defaults to configured project)
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().storage
            project_id = project_id or client_instances.get_project_id()

            # Get bucket and blob
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)

            print(f"Deleting gs://{bucket_name}/{blob_name}...")

            # Delete the blob
            blob.delete()

            return json.dumps(
                {
                    "status": "success",
                    "message": f"Successfully deleted gs://{bucket_name}/{blob_name}",
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    # Prompts
    @mcp_instance.prompt()
    def create_bucket_prompt(location: str = "us-central1") -> str:
        """Prompt for creating a new Cloud Storage bucket"""
        return f"""
I need to create a new Cloud Storage bucket in {location}.

Please help me with:
1. Understanding storage classes (STANDARD, NEARLINE, COLDLINE, ARCHIVE)
2. Best practices for bucket naming
3. When to enable versioning
4. Recommendations for bucket security settings
5. Steps to create the bucket
"""

    @mcp_instance.prompt()
    def upload_file_prompt() -> str:
        """Prompt for help with uploading files to Cloud Storage"""
        return """
I need to upload files to a Cloud Storage bucket.

Please help me understand:
1. The best way to organize files in Cloud Storage
2. When to use folders/prefixes
3. How to set appropriate permissions on uploaded files
4. How to make files publicly accessible (if needed)
5. The steps to perform the upload
"""
