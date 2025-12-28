"""Instrumented Ollama client with OpenTelemetry tracing."""

import json
import logging
import time
from typing import Any, AsyncIterator

import ollama
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from app.domain.exceptions import OllamaError
from app.infrastructure.telemetry import create_ollama_span, get_tracer

logger = logging.getLogger(__name__)


class InstrumentedOllamaClient:
    """Ollama client with OpenTelemetry instrumentation for Phoenix."""

    def __init__(self, host: str, model: str) -> None:
        """Initialize the instrumented Ollama client.

        Args:
            host: Ollama API host URL
            model: Model name to use (e.g., "llama3.1:8b")
        """
        self.host = host
        self.model = model
        self._client = ollama.AsyncClient(host=host)
        self._tracer = get_tracer()

    async def verify_connection(self) -> bool:
        """Verify connection to Ollama with tracing.

        Returns:
            True if connection is successful

        Raises:
            OllamaError: If connection fails
        """
        with self._tracer.start_as_current_span(
            "ollama.verify_connection",
            kind=trace.SpanKind.CLIENT,
        ) as span:
            span.set_attribute("llm.vendor", "ollama")
            span.set_attribute("llm.model", self.model)
            span.set_attribute("llm.host", self.host)

            try:
                start_time = time.time()
                models_response = await self._client.list()
                duration_ms = (time.time() - start_time) * 1000

                # Extract available models
                if hasattr(models_response, 'models'):
                    models_list = models_response.models
                elif isinstance(models_response, dict):
                    models_list = models_response.get("models", [])
                else:
                    models_list = []

                available_models = []
                for model in models_list:
                    if hasattr(model, 'model'):
                        available_models.append(model.model)
                    elif isinstance(model, dict):
                        available_models.append(model.get('model', model.get('name', '')))

                span.set_attribute("llm.available_models_count", len(available_models))
                span.set_attribute("llm.duration_ms", duration_ms)

                logger.info(f"Available Ollama models: {available_models}")

                if self.model not in available_models:
                    error_msg = f"Model '{self.model}' not available. Please pull it with: ollama pull {self.model}"
                    span.set_status(Status(StatusCode.ERROR, error_msg))
                    span.record_exception(OllamaError(error_msg))
                    raise OllamaError(error_msg)

                span.set_status(Status(StatusCode.OK))
                logger.info(f"Successfully connected to Ollama with model '{self.model}'")
                return True

            except ollama.ResponseError as e:
                error_msg = f"Failed to connect to Ollama: {e}"
                span.set_status(Status(StatusCode.ERROR, error_msg))
                span.record_exception(e)
                logger.error(error_msg)
                raise OllamaError(error_msg) from e
            except OllamaError:
                raise
            except Exception as e:
                error_msg = f"Unexpected error: {e}"
                span.set_status(Status(StatusCode.ERROR, error_msg))
                span.record_exception(e)
                logger.error(error_msg)
                raise OllamaError(error_msg) from e

    async def chat_with_tools(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Chat with tools using OpenTelemetry tracing.

        Args:
            messages: Conversation messages
            tools: Available tools

        Returns:
            Response dictionary

        Raises:
            OllamaError: If chat fails
        """
        span = create_ollama_span(
            operation="chat_with_tools",
            model=self.model,
            message_count=len(messages),
            tool_count=len(tools),
            host=self.host,
        )

        try:
            # Record message details
            if messages:
                last_message = messages[-1]
                span.set_attribute("llm.last_message_role", last_message.get("role", ""))
                content = last_message.get("content", "")
                if isinstance(content, str):
                    span.set_attribute("llm.last_message_length", len(content))
                    # Truncate content for span attribute (limit to 1000 chars)
                    span.set_attribute("llm.last_message_preview", content[:1000])

            # Record tool names
            tool_names = [t.get("function", {}).get("name", "") for t in tools]
            span.set_attribute("llm.available_tools", json.dumps(tool_names))

            logger.debug(f"Sending chat request with {len(messages)} messages and {len(tools)} tools")

            # Make the request and measure time
            start_time = time.time()
            response = await self._client.chat(
                model=self.model,
                messages=messages,
                tools=tools,
            )
            duration_ms = (time.time() - start_time) * 1000

            # Record response details
            span.set_attribute("llm.duration_ms", duration_ms)

            if response and "message" in response:
                response_msg = response["message"]

                # Record response content
                if "content" in response_msg:
                    content = response_msg["content"]
                    span.set_attribute("llm.response_length", len(content))
                    span.set_attribute("llm.response_preview", content[:1000])

                # Record tool calls
                if "tool_calls" in response_msg:
                    tool_calls = response_msg["tool_calls"]
                    span.set_attribute("llm.tool_calls_count", len(tool_calls))
                    called_tools = [
                        tc.get("function", {}).get("name", "")
                        for tc in tool_calls
                    ]
                    span.set_attribute("llm.called_tools", json.dumps(called_tools))

                # Record token usage if available
                if "eval_count" in response:
                    span.set_attribute("llm.tokens_output", response["eval_count"])
                if "prompt_eval_count" in response:
                    span.set_attribute("llm.tokens_input", response["prompt_eval_count"])
                if "total_duration" in response:
                    total_duration_ms = response["total_duration"] / 1_000_000  # ns to ms
                    span.set_attribute("llm.total_duration_ms", total_duration_ms)

            span.set_status(Status(StatusCode.OK))
            logger.debug(f"Received response in {duration_ms:.2f}ms")
            return response

        except ollama.ResponseError as e:
            error_msg = f"Ollama chat failed: {e}"
            span.set_status(Status(StatusCode.ERROR, error_msg))
            span.record_exception(e)
            logger.error(error_msg)
            raise OllamaError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            span.set_status(Status(StatusCode.ERROR, error_msg))
            span.record_exception(e)
            logger.error(error_msg)
            raise OllamaError(error_msg) from e
        finally:
            span.end()

    async def chat_streaming(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None
    ) -> AsyncIterator[str]:
        """Chat with streaming and tracing.

        Args:
            messages: Conversation messages
            tools: Optional tools

        Yields:
            Response chunks

        Raises:
            OllamaError: If streaming fails
        """
        span = create_ollama_span(
            operation="chat_streaming",
            model=self.model,
            message_count=len(messages),
            tool_count=len(tools) if tools else 0,
            host=self.host,
        )

        try:
            # Record message details
            if messages:
                last_message = messages[-1]
                span.set_attribute("llm.last_message_role", last_message.get("role", ""))

            logger.debug(f"Starting streaming chat with {len(messages)} messages")

            kwargs: dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "stream": True,
            }
            if tools:
                kwargs["tools"] = tools

            start_time = time.time()
            chunk_count = 0
            total_content_length = 0

            async for chunk in await self._client.chat(**kwargs):
                chunk_count += 1

                if "message" in chunk:
                    message = chunk["message"]

                    if "content" in message and message["content"]:
                        content = message["content"]
                        total_content_length += len(content)
                        yield content

                    if "tool_calls" in message and message["tool_calls"]:
                        logger.debug(f"Tool calls detected in streaming: {message['tool_calls']}")
                        span.set_attribute("llm.has_tool_calls", True)

            duration_ms = (time.time() - start_time) * 1000

            # Record streaming metrics
            span.set_attribute("llm.duration_ms", duration_ms)
            span.set_attribute("llm.chunk_count", chunk_count)
            span.set_attribute("llm.total_content_length", total_content_length)
            span.set_status(Status(StatusCode.OK))

        except ollama.ResponseError as e:
            error_msg = f"Ollama streaming failed: {e}"
            span.set_status(Status(StatusCode.ERROR, error_msg))
            span.record_exception(e)
            logger.error(error_msg)
            raise OllamaError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            span.set_status(Status(StatusCode.ERROR, error_msg))
            span.record_exception(e)
            logger.error(error_msg)
            raise OllamaError(error_msg) from e
        finally:
            span.end()
