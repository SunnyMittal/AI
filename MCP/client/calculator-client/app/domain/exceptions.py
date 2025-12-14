"""Custom exceptions for the calculator client."""


class CalculatorClientError(Exception):
    """Base exception for all calculator client errors."""

    pass


class MCPConnectionError(CalculatorClientError):
    """Raised when connection to MCP server fails."""

    pass


class ToolNotFoundError(CalculatorClientError):
    """Raised when a requested tool is not found in the registry."""

    pass


class ToolExecutionError(CalculatorClientError):
    """Raised when tool execution fails."""

    pass


class OllamaError(CalculatorClientError):
    """Raised when Ollama API communication fails."""

    pass


class ConfigurationError(CalculatorClientError):
    """Raised when configuration is invalid or missing."""

    pass
