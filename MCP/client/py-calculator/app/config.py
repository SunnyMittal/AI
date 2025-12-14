"""Application configuration management using Pydantic Settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    mcp_server_url: str = Field(
        default="http://127.0.0.1:8000/mcp", description="HTTP URL for the MCP server"
    )

    mcp_server_path: str = Field(
        default="D:/AI/MCP/server/calculator", description="Path to the MCP calculator server"
    )

    mcp_python_path: str = Field(
        default="D:/AI/MCP/server/calculator/.venv/Scripts/python.exe",
        description="Python executable path for MCP server",
    )

    ollama_host: str = Field(
        default="http://localhost:11434", description="Ollama API host URL"
    )

    ollama_model: str = Field(
        default="codellama:34b-instruct", description="Ollama model to use for chat"
    )

    log_level: str = Field(default="INFO", description="Logging level")

    cors_origins: str = Field(default="*", description="CORS allowed origins (comma-separated)")

    max_conversation_history: int = Field(
        default=50, description="Maximum number of messages to keep in conversation history"
    )

    host: str = Field(default="0.0.0.0", description="Server host")

    port: int = Field(default=8000, description="Server port")

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
