"""Utility functions for MCP server."""

import json
from typing import Any


def format_json_response(data: Any) -> str:
    """Format data as a JSON string with consistent styling."""
    return json.dumps({"status": "success", "data": data}, indent=2)


def format_error_response(message: str) -> str:
    """Format error message as a JSON string."""
    return json.dumps({"status": "error", "message": message}, indent=2)
