import logging


class MCPLogger:
    """Simple logger for MCP server"""

    def __init__(self, name):
        self.logger = logging.getLogger(f"mcp.{name}")

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)

    def debug(self, message):
        self.logger.debug(message)

    def audit_log(self, action, resource, details=None):
        """Simple audit logging"""
        self.logger.info(f"AUDIT: {action} on {resource}")
