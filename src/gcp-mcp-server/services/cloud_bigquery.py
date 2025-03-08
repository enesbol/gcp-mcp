import json
from typing import Any, Dict, List, Optional

from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from services import client_instances


def register(mcp_instance):
    """Register all BigQuery resources and tools with the MCP instance."""

    # Resources
    @mcp_instance.resource("gcp://bigquery/{project_id}/datasets")
    def list_datasets_resource(project_id: str = None) -> str:
        """List all BigQuery datasets in a project"""
        try:
            # Get client from client_instances
            client = client_instances.get_clients().bigquery
            project_id = project_id or client_instances.get_project_id()

            datasets = list(client.list_datasets())

            result = []
            for dataset in datasets:
                result.append(
                    {
                        "id": dataset.dataset_id,
                        "full_id": dataset.full_dataset_id,
                        "friendly_name": dataset.friendly_name,
                        "location": dataset.location,
                        "labels": dict(dataset.labels) if dataset.labels else {},
                        "created": dataset.created.isoformat()
                        if dataset.created
                        else None,
                    }
                )

            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    @mcp_instance.resource("gcp://bigquery/{project_id}/dataset/{dataset_id}")
    def get_dataset_resource(project_id: str = None, dataset_id: str = None) -> str:
        """Get details for a specific BigQuery dataset"""
        try:
            # Get client from client_instances
            client = client_instances.get_clients().bigquery
            project_id = project_id or client_instances.get_project_id()

            dataset_ref = client.dataset(dataset_id)
            dataset = client.get_dataset(dataset_ref)

            result = {
                "id": dataset.dataset_id,
                "full_id": dataset.full_dataset_id,
                "friendly_name": dataset.friendly_name,
                "description": dataset.description,
                "location": dataset.location,
                "labels": dict(dataset.labels) if dataset.labels else {},
                "created": dataset.created.isoformat() if dataset.created else None,
                "modified": dataset.modified.isoformat() if dataset.modified else None,
                "default_table_expiration_ms": dataset.default_table_expiration_ms,
                "default_partition_expiration_ms": dataset.default_partition_expiration_ms,
            }
            return json.dumps(result, indent=2)
        except NotFound:
            return json.dumps({"error": f"Dataset {dataset_id} not found"}, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    @mcp_instance.resource("gcp://bigquery/{project_id}/dataset/{dataset_id}/tables")
    def list_tables_resource(project_id: str = None, dataset_id: str = None) -> str:
        """List all tables in a BigQuery dataset"""
        try:
            # Get client from client_instances
            client = client_instances.get_clients().bigquery
            project_id = project_id or client_instances.get_project_id()

            tables = list(client.list_tables(dataset_id))

            result = []
            for table in tables:
                result.append(
                    {
                        "id": table.table_id,
                        "full_id": f"{table.project}.{table.dataset_id}.{table.table_id}",
                        "table_type": table.table_type,
                    }
                )

            return json.dumps(result, indent=2)
        except NotFound:
            return json.dumps({"error": f"Dataset {dataset_id} not found"}, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    @mcp_instance.resource(
        "gcp://bigquery/{project_id}/dataset/{dataset_id}/table/{table_id}"
    )
    def get_table_resource(
        project_id: str = None, dataset_id: str = None, table_id: str = None
    ) -> str:
        """Get details for a specific BigQuery table"""
        try:
            # Get client from client_instances
            client = client_instances.get_clients().bigquery
            project_id = project_id or client_instances.get_project_id()

            table_ref = client.dataset(dataset_id).table(table_id)
            table = client.get_table(table_ref)

            # Extract schema information
            schema_fields = []
            for field in table.schema:
                schema_fields.append(
                    {
                        "name": field.name,
                        "type": field.field_type,
                        "mode": field.mode,
                        "description": field.description,
                    }
                )

            result = {
                "id": table.table_id,
                "full_id": f"{table.project}.{table.dataset_id}.{table.table_id}",
                "friendly_name": table.friendly_name,
                "description": table.description,
                "num_rows": table.num_rows,
                "num_bytes": table.num_bytes,
                "table_type": table.table_type,
                "created": table.created.isoformat() if table.created else None,
                "modified": table.modified.isoformat() if table.modified else None,
                "expires": table.expires.isoformat() if table.expires else None,
                "schema": schema_fields,
                "labels": dict(table.labels) if table.labels else {},
            }
            return json.dumps(result, indent=2)
        except NotFound:
            return json.dumps(
                {"error": f"Table {dataset_id}.{table_id} not found"}, indent=2
            )
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    # Tools
    @mcp_instance.tool()
    def run_query(
        query: str,
        project_id: str = None,
        location: str = None,
        max_results: int = 100,
        use_legacy_sql: bool = False,
        timeout_ms: int = 30000,
    ) -> str:
        """
        Run a BigQuery query and return the results

        Args:
            query: SQL query to execute
            project_id: GCP project ID (defaults to configured project)
            location: Optional BigQuery location (us, eu, etc.)
            max_results: Maximum number of rows to return
            use_legacy_sql: Whether to use legacy SQL syntax
            timeout_ms: Query timeout in milliseconds
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().bigquery
            project_id = project_id or client_instances.get_project_id()
            location = location or client_instances.get_location()

            job_config = bigquery.QueryJobConfig(
                use_legacy_sql=use_legacy_sql,
            )

            # Log info (similar to ctx.info)
            print(f"Running query: {query[:100]}...")

            query_job = client.query(
                query,
                job_config=job_config,
                location=location,
                timeout=timeout_ms / 1000.0,
            )

            # Wait for the query to complete
            results = query_job.result(max_results=max_results)

            # Get the schema
            schema = [field.name for field in results.schema]

            # Convert rows to a list of dictionaries
            rows = []
            for row in results:
                row_dict = {}
                for key in schema:
                    value = row[key]
                    if hasattr(value, "isoformat"):  # Handle datetime objects
                        row_dict[key] = value.isoformat()
                    else:
                        row_dict[key] = value
                rows.append(row_dict)

            # Create summary statistics
            stats = {
                "total_rows": query_job.total_rows,
                "total_bytes_processed": query_job.total_bytes_processed,
                "total_bytes_billed": query_job.total_bytes_billed,
                "billing_tier": query_job.billing_tier,
                "created": query_job.created.isoformat() if query_job.created else None,
                "started": query_job.started.isoformat() if query_job.started else None,
                "ended": query_job.ended.isoformat() if query_job.ended else None,
                "duration_ms": (query_job.ended - query_job.started).total_seconds()
                * 1000
                if query_job.started and query_job.ended
                else None,
            }

            return json.dumps(
                {
                    "status": "success",
                    "schema": schema,
                    "rows": rows,
                    "returned_rows": len(rows),
                    "stats": stats,
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def create_dataset(
        dataset_id: str,
        project_id: str = None,
        location: str = None,
        description: str = "",
        friendly_name: str = None,
        labels: Optional[Dict[str, str]] = None,
        default_table_expiration_ms: Optional[int] = None,
    ) -> str:
        """
        Create a new BigQuery dataset

        Args:
            dataset_id: ID for the new dataset
            project_id: GCP project ID (defaults to configured project)
            location: Dataset location (US, EU, asia-northeast1, etc.)
            description: Optional dataset description
            friendly_name: Optional user-friendly name
            labels: Optional key-value pairs for dataset labels
            default_table_expiration_ms: Default expiration time for tables in milliseconds
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().bigquery
            project_id = project_id or client_instances.get_project_id()
            location = location or client_instances.get_location()

            dataset = bigquery.Dataset(f"{project_id}.{dataset_id}")
            dataset.location = location

            if description:
                dataset.description = description
            if friendly_name:
                dataset.friendly_name = friendly_name
            if labels:
                dataset.labels = labels
            if default_table_expiration_ms:
                dataset.default_table_expiration_ms = default_table_expiration_ms

            # Log info (similar to ctx.info)
            print(f"Creating dataset {dataset_id} in {location}...")
            dataset = client.create_dataset(dataset)

            return json.dumps(
                {
                    "status": "success",
                    "dataset_id": dataset.dataset_id,
                    "full_dataset_id": dataset.full_dataset_id,
                    "location": dataset.location,
                    "created": dataset.created.isoformat() if dataset.created else None,
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def create_table(
        dataset_id: str,
        table_id: str,
        schema_fields: List[Dict[str, Any]],
        project_id: str = None,
        description: str = "",
        friendly_name: str = None,
        expiration_ms: Optional[int] = None,
        labels: Optional[Dict[str, str]] = None,
        clustering_fields: Optional[List[str]] = None,
        time_partitioning_field: Optional[str] = None,
        time_partitioning_type: str = "DAY",
    ) -> str:
        """
        Create a new BigQuery table

        Args:
            dataset_id: Dataset ID where the table will be created
            table_id: ID for the new table
            schema_fields: List of field definitions, each with name, type, mode, and description
            project_id: GCP project ID (defaults to configured project)
            description: Optional table description
            friendly_name: Optional user-friendly name
            expiration_ms: Optional table expiration time in milliseconds
            labels: Optional key-value pairs for table labels
            clustering_fields: Optional list of fields to cluster by
            time_partitioning_field: Optional field to use for time-based partitioning
            time_partitioning_type: Partitioning type (DAY, HOUR, MONTH, YEAR)

        Example schema_fields:
        [
            {"name": "name", "type": "STRING", "mode": "REQUIRED", "description": "Name field"},
            {"name": "age", "type": "INTEGER", "mode": "NULLABLE", "description": "Age field"}
        ]
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().bigquery
            project_id = project_id or client_instances.get_project_id()

            # Convert schema_fields to SchemaField objects
            schema = []
            for field in schema_fields:
                schema.append(
                    bigquery.SchemaField(
                        name=field["name"],
                        field_type=field["type"],
                        mode=field.get("mode", "NULLABLE"),
                        description=field.get("description", ""),
                    )
                )

            # Create table reference
            table_ref = client.dataset(dataset_id).table(table_id)
            table = bigquery.Table(table_ref, schema=schema)

            # Set table properties
            if description:
                table.description = description
            if friendly_name:
                table.friendly_name = friendly_name
            if expiration_ms:
                table.expires = expiration_ms
            if labels:
                table.labels = labels

            # Set clustering if specified
            if clustering_fields:
                table.clustering_fields = clustering_fields

            # Set time partitioning if specified
            if time_partitioning_field:
                if time_partitioning_type == "DAY":
                    table.time_partitioning = bigquery.TimePartitioning(
                        type_=bigquery.TimePartitioningType.DAY,
                        field=time_partitioning_field,
                    )
                elif time_partitioning_type == "HOUR":
                    table.time_partitioning = bigquery.TimePartitioning(
                        type_=bigquery.TimePartitioningType.HOUR,
                        field=time_partitioning_field,
                    )
                elif time_partitioning_type == "MONTH":
                    table.time_partitioning = bigquery.TimePartitioning(
                        type_=bigquery.TimePartitioningType.MONTH,
                        field=time_partitioning_field,
                    )
                elif time_partitioning_type == "YEAR":
                    table.time_partitioning = bigquery.TimePartitioning(
                        type_=bigquery.TimePartitioningType.YEAR,
                        field=time_partitioning_field,
                    )

            # Log info (similar to ctx.info)
            print(f"Creating table {dataset_id}.{table_id}...")
            table = client.create_table(table)

            return json.dumps(
                {
                    "status": "success",
                    "table_id": table.table_id,
                    "full_table_id": f"{table.project}.{table.dataset_id}.{table.table_id}",
                    "created": table.created.isoformat() if table.created else None,
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def delete_table(dataset_id: str, table_id: str, project_id: str = None) -> str:
        """
        Delete a BigQuery table

        Args:
            dataset_id: Dataset ID containing the table
            table_id: ID of the table to delete
            project_id: GCP project ID (defaults to configured project)
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().bigquery
            project_id = project_id or client_instances.get_project_id()

            table_ref = client.dataset(dataset_id).table(table_id)

            # Log info (similar to ctx.info)
            print(f"Deleting table {dataset_id}.{table_id}...")
            client.delete_table(table_ref)

            return json.dumps(
                {
                    "status": "success",
                    "message": f"Table {project_id}.{dataset_id}.{table_id} successfully deleted",
                },
                indent=2,
            )
        except NotFound:
            return json.dumps(
                {
                    "status": "error",
                    "message": f"Table {project_id}.{dataset_id}.{table_id} not found",
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def load_table_from_json(
        dataset_id: str,
        table_id: str,
        json_data: List[Dict[str, Any]],
        project_id: str = None,
        schema_fields: Optional[List[Dict[str, Any]]] = None,
        write_disposition: str = "WRITE_APPEND",
    ) -> str:
        """
        Load data into a BigQuery table from JSON data

        Args:
            dataset_id: Dataset ID containing the table
            table_id: ID of the table to load data into
            json_data: List of dictionaries representing rows to insert
            project_id: GCP project ID (defaults to configured project)
            schema_fields: Optional schema definition (if not using existing table schema)
            write_disposition: How to handle existing data (WRITE_TRUNCATE, WRITE_APPEND, WRITE_EMPTY)
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().bigquery
            project_id = project_id or client_instances.get_project_id()

            table_ref = client.dataset(dataset_id).table(table_id)

            # Convert write_disposition to the appropriate enum
            if write_disposition == "WRITE_TRUNCATE":
                disposition = bigquery.WriteDisposition.WRITE_TRUNCATE
            elif write_disposition == "WRITE_APPEND":
                disposition = bigquery.WriteDisposition.WRITE_APPEND
            elif write_disposition == "WRITE_EMPTY":
                disposition = bigquery.WriteDisposition.WRITE_EMPTY
            else:
                return json.dumps(
                    {
                        "status": "error",
                        "message": f"Invalid write_disposition: {write_disposition}. Use WRITE_TRUNCATE, WRITE_APPEND, or WRITE_EMPTY.",
                    },
                    indent=2,
                )

            # Create job config
            job_config = bigquery.LoadJobConfig(
                write_disposition=disposition,
                source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            )

            # Set schema if provided
            if schema_fields:
                schema = []
                for field in schema_fields:
                    schema.append(
                        bigquery.SchemaField(
                            name=field["name"],
                            field_type=field["type"],
                            mode=field.get("mode", "NULLABLE"),
                            description=field.get("description", ""),
                        )
                    )
                job_config.schema = schema

            # Convert JSON data to newline-delimited JSON (not needed but keeping the log)
            print(f"Loading {len(json_data)} rows into {dataset_id}.{table_id}...")

            # Create and run the load job
            load_job = client.load_table_from_json(
                json_data, table_ref, job_config=job_config
            )

            # Wait for the job to complete
            load_job.result()

            # Get updated table info
            table = client.get_table(table_ref)

            return json.dumps(
                {
                    "status": "success",
                    "rows_loaded": len(json_data),
                    "total_rows": table.num_rows,
                    "message": f"Successfully loaded data into {project_id}.{dataset_id}.{table_id}",
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @mcp_instance.tool()
    def export_table_to_csv(
        dataset_id: str,
        table_id: str,
        destination_uri: str,
        project_id: str = None,
        print_header: bool = True,
        field_delimiter: str = ",",
    ) -> str:
        """
        Export a BigQuery table to Cloud Storage as CSV

        Args:
            dataset_id: Dataset ID containing the table
            table_id: ID of the table to export
            destination_uri: GCS URI (gs://bucket/path)
            project_id: GCP project ID (defaults to configured project)
            print_header: Whether to include column headers
            field_delimiter: Delimiter character for fields
        """
        try:
            # Get client from client_instances
            client = client_instances.get_clients().bigquery
            project_id = project_id or client_instances.get_project_id()

            table_ref = client.dataset(dataset_id).table(table_id)

            # Validate destination URI
            if not destination_uri.startswith("gs://"):
                return json.dumps(
                    {
                        "status": "error",
                        "message": "destination_uri must start with gs://",
                    },
                    indent=2,
                )

            job_config = bigquery.ExtractJobConfig()
            job_config.destination_format = bigquery.DestinationFormat.CSV
            job_config.print_header = print_header
            job_config.field_delimiter = field_delimiter

            # Log info (similar to ctx.info)
            print(f"Exporting {dataset_id}.{table_id} to {destination_uri}...")

            # Create and run the extract job
            extract_job = client.extract_table(
                table_ref, destination_uri, job_config=job_config
            )

            # Wait for the job to complete
            extract_job.result()

            return json.dumps(
                {
                    "status": "success",
                    "destination": destination_uri,
                    "message": f"Successfully exported {project_id}.{dataset_id}.{table_id} to {destination_uri}",
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    # Prompts
    @mcp_instance.prompt()
    def create_dataset_prompt() -> str:
        """Prompt for creating a new BigQuery dataset"""
        return """
I need to create a new BigQuery dataset.

Please help me with:
1. Choosing an appropriate location for my dataset
2. Understanding dataset naming conventions
3. Best practices for dataset configuration (expiration, labels, etc.)
4. The process to create the dataset
"""

    @mcp_instance.prompt()
    def query_optimization_prompt() -> str:
        """Prompt for BigQuery query optimization help"""
        return """
I have a BigQuery query that's slow or expensive to run.

Please help me optimize it by:
1. Analyzing key factors that affect BigQuery performance
2. Identifying common patterns that lead to inefficient queries
3. Suggesting specific optimization techniques
4. Helping me understand how to use EXPLAIN plan analysis
"""
