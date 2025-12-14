"""Ollama client adapter for LLM interactions with function calling."""

import logging
from typing import Any, AsyncIterator, Protocol

import ollama

from app.domain.exceptions import OllamaError

logger = logging.getLogger(__name__)


class OllamaAdapter(Protocol):
    """Protocol defining the Ollama client interface."""

    async def chat_with_tools(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Chat with the LLM using function calling."""
        ...

    async def chat_streaming(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None
    ) -> AsyncIterator[str]:
        """Chat with streaming responses."""
        ...


class OllamaClientImpl:
    """Ollama client implementation with function calling support."""

    def __init__(self, host: str, model: str) -> None:
        """Initialize the Ollama client.

        Args:
            host: Ollama API host URL
            model: Model name to use (e.g., "llama3.1:8b")
        """
        self.host = host
        self.model = model
        self._client = ollama.AsyncClient(host=host)

    async def verify_connection(self) -> bool:
        """Verify connection to Ollama and model availability.

        Returns:
            True if connection is successful and model is available

        Raises:
            OllamaError: If connection fails or model is not available
        """
        try:
            models_response = await self._client.list()

            # Handle both dict and object responses
            if hasattr(models_response, 'models'):
                models_list = models_response.models
            elif isinstance(models_response, dict):
                models_list = models_response.get("models", [])
            else:
                models_list = []

            # Extract model names, handling both dict and object formats
            available_models = []
            for model in models_list:
                if hasattr(model, 'model'):
                    available_models.append(model.model)
                elif isinstance(model, dict):
                    available_models.append(model.get('model', model.get('name', '')))

            logger.info(f"Available Ollama models: {available_models}")

            if self.model not in available_models:
                logger.warning(
                    f"Model '{self.model}' not found. Available models: {available_models}"
                )
                raise OllamaError(
                    f"Model '{self.model}' not available. Please pull it with: ollama pull {self.model}"
                )

            logger.info(f"Successfully connected to Ollama with model '{self.model}'")
            return True

        except ollama.ResponseError as e:
            logger.error(f"Ollama connection error: {e}")
            raise OllamaError(f"Failed to connect to Ollama: {e}") from e
        except OllamaError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error verifying Ollama connection: {e}")
            raise OllamaError(f"Unexpected error: {e}") from e

    async def chat_with_tools(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Chat with the LLM using function calling.

        Args:
            messages: Conversation messages in Ollama format
            tools: Available tools in Ollama function format

        Returns:
            Response dictionary containing message and optional tool calls

        Raises:
            OllamaError: If the chat request fails
        """
        try:
            logger.debug(f"Sending chat request with {len(messages)} messages and {len(tools)} tools")

            response = await self._client.chat(
                model=self.model, messages=messages, tools=tools
            )

            logger.debug(f"Received response: {response}")
            return response

        except ollama.ResponseError as e:
            logger.error(f"Ollama chat error: {e}")
            raise OllamaError(f"Ollama chat failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during chat: {e}")
            raise OllamaError(f"Unexpected error: {e}") from e

    async def chat_streaming(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None
    ) -> AsyncIterator[str]:
        """Chat with streaming responses.

        Args:
            messages: Conversation messages in Ollama format
            tools: Optional available tools in Ollama function format

        Yields:
            Response chunks as they arrive

        Raises:
            OllamaError: If the streaming request fails
        """
        try:
            logger.debug(f"Starting streaming chat with {len(messages)} messages")

            kwargs: dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "stream": True,
            }
            if tools:
                kwargs["tools"] = tools

            async for chunk in await self._client.chat(**kwargs):
                if "message" in chunk:
                    message = chunk["message"]
                    if "content" in message and message["content"]:
                        yield message["content"]

                    if "tool_calls" in message and message["tool_calls"]:
                        logger.debug(f"Tool calls detected in streaming: {message['tool_calls']}")

        except ollama.ResponseError as e:
            logger.error(f"Ollama streaming error: {e}")
            raise OllamaError(f"Ollama streaming failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during streaming: {e}")
            raise OllamaError(f"Unexpected error: {e}") from e
