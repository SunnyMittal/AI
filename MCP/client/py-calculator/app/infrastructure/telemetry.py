"""OpenTelemetry instrumentation for Ollama client."""

import logging
import os
from typing import Any

from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Global tracer instance
_tracer: trace.Tracer | None = None


def initialize_telemetry() -> trace.Tracer:
    """Initialize OpenTelemetry with Phoenix backend using environment configuration.

    Environment variables:
        OTEL_SERVICE_NAME: Name of the service for telemetry (default: "ollama-client")
        PHOENIX_ENDPOINT: Phoenix OTLP endpoint URL (default: "http://localhost:6006/v1/traces")
        PHOENIX_PROJECT_NAME: Phoenix project name for classification (default: "default")
        ENVIRONMENT: Deployment environment (default: "development")
        SERVICE_VERSION: Service version (default: "1.0.0")

    Returns:
        Configured tracer instance
    """
    global _tracer

    if _tracer is not None:
        return _tracer

    try:
        # Read configuration from environment
        service_name = os.getenv("OTEL_SERVICE_NAME", "ollama-client")
        phoenix_endpoint = os.getenv(
            "PHOENIX_ENDPOINT", "http://localhost:6006/v1/traces"
        )
        phoenix_project_name = os.getenv("PHOENIX_PROJECT_NAME", "default")
        environment = os.getenv("ENVIRONMENT", "development")
        service_version = os.getenv("SERVICE_VERSION", "1.0.0")

        # Create resource with service information
        resource = Resource.create(
            {
                "service.name": service_name,
                "service.version": service_version,
                "deployment.environment": environment,
                "phoenix.project.name": phoenix_project_name,
            }
        )

        # Create tracer provider
        provider = TracerProvider(resource=resource)

        # Configure OTLP exporter for Phoenix with custom headers
        headers = {
            "x-phoenix-project-name": phoenix_project_name,
        }

        otlp_exporter = OTLPSpanExporter(
            endpoint=phoenix_endpoint,
            headers=headers,
            timeout=30,
        )

        # Add batch span processor
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

        # Set global tracer provider
        trace.set_tracer_provider(provider)

        # Get tracer instance
        _tracer = trace.get_tracer(__name__)

        logger.info(
            f"Telemetry initialized: service={service_name}, "
            f"project={phoenix_project_name}, "
            f"endpoint={phoenix_endpoint}, "
            f"env={environment}"
        )
        return _tracer

    except Exception as e:
        logger.warning(f"Failed to initialize telemetry: {e}. Continuing without tracing.")
        # Return no-op tracer
        return trace.get_tracer(__name__)


def get_tracer() -> trace.Tracer:
    """Get the global tracer instance.

    Returns:
        Tracer instance (initialized or no-op)
    """
    global _tracer

    if _tracer is None:
        _tracer = initialize_telemetry()

    return _tracer


def create_ollama_span(
    operation: str,
    model: str,
    message_count: int,
    tool_count: int = 0,
    **attributes: Any,
) -> trace.Span:
    """Create a span for Ollama operations.

    Args:
        operation: Operation name (e.g., "chat", "chat_streaming")
        model: LLM model name
        message_count: Number of messages in conversation
        tool_count: Number of tools available
        **attributes: Additional span attributes

    Returns:
        Started span
    """
    tracer = get_tracer()

    span = tracer.start_span(
        name=f"ollama.{operation}",
        kind=trace.SpanKind.CLIENT,
    )

    # Set standard attributes
    span.set_attribute("llm.vendor", "ollama")
    span.set_attribute("llm.model", model)
    span.set_attribute("llm.operation", operation)
    span.set_attribute("llm.message_count", message_count)
    span.set_attribute("llm.tool_count", tool_count)

    # Set custom attributes
    for key, value in attributes.items():
        if isinstance(value, (str, int, float, bool)):
            span.set_attribute(f"llm.{key}", value)

    return span
