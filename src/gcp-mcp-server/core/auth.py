import json
import os

import google.auth
from google.auth.exceptions import DefaultCredentialsError
from google.auth.transport.requests import Request
from google.oauth2 import service_account

from .logging_handler import MCPLogger

# Define required scopes for GCP APIs
REQUIRED_SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
]

logger = MCPLogger("auth")


def get_credentials():
    """
    Get Google Cloud credentials from environment.
    Attempts to load credentials in the following order:
    1. From GOOGLE_APPLICATION_CREDENTIALS environment variable
    2. From GCP_SERVICE_ACCOUNT_JSON environment variable containing JSON
    3. Default application credentials
    """
    try:
        # Check for credentials file path
        creds_file = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if creds_file and os.path.exists(creds_file):
            logger.audit_log(
                action="credential_load",
                resource="service_account",
                details={"method": "file", "file": creds_file},
            )
            logger.info(f"Loading credentials from file: {creds_file}")
            credentials = service_account.Credentials.from_service_account_file(
                creds_file, scopes=REQUIRED_SCOPES
            )
            return validate_credentials(credentials)

        # Check for service account JSON in environment
        sa_json = os.environ.get("GCP_SERVICE_ACCOUNT_JSON")
        if sa_json:
            try:
                service_account_info = json.loads(sa_json)
                logger.info(
                    "Loading credentials from GCP_SERVICE_ACCOUNT_JSON environment variable"
                )
                credentials = service_account.Credentials.from_service_account_info(
                    service_account_info, scopes=REQUIRED_SCOPES
                )
                logger.audit_log(
                    action="credential_load",
                    resource="service_account",
                    details={"method": "environment_json"},
                )
                return validate_credentials(credentials)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse GCP_SERVICE_ACCOUNT_JSON: {str(e)}")

        # Fall back to default credentials
        try:
            logger.audit_log(
                action="credential_load",
                resource="application_default",
                details={"method": "default"},
            )
            logger.info("Loading default application credentials")
            credentials, project_id = google.auth.default(scopes=REQUIRED_SCOPES)
            if project_id and not os.environ.get("GCP_PROJECT_ID"):
                # Set project ID from default credentials if not already set
                os.environ["GCP_PROJECT_ID"] = project_id
                logger.info(f"Using project ID from default credentials: {project_id}")
            return validate_credentials(credentials)
        except DefaultCredentialsError as e:
            logger.error(f"Failed to load GCP credentials: {str(e)}")
            raise AuthenticationError("Failed to obtain valid credentials")

    except Exception as e:
        logger.critical(f"Authentication failure: {str(e)}")
        raise AuthenticationError(f"Failed to obtain valid credentials: {str(e)}")


def validate_credentials(credentials):
    """Validate credential permissions and expiration"""
    # Some credentials don't have a valid attribute or may not need refresh
    if hasattr(credentials, "valid") and not credentials.valid:
        credentials.refresh(Request())

    # Check expiration
    if hasattr(credentials, "expiry"):
        if hasattr(credentials, "expired") and credentials.expired:
            try:
                credentials.refresh(Request())
            except Exception as e:
                raise AuthenticationError(
                    f"Failed to refresh expired credentials: {str(e)}"
                )

    return credentials


class AuthenticationError(Exception):
    """Custom exception for authentication failures"""

    pass
