"""
GCP MCP Server services package.
This package contains service modules that register tools and resources with the MCP server.
"""

import importlib
import pkgutil
from pathlib import Path


def load_services() -> None:
    """Dynamically load all service modules."""
    package_dir = Path(__file__).parent
    for _, module_name, _ in pkgutil.iter_modules([str(package_dir)]):
        importlib.import_module(f".{module_name}", __package__)
