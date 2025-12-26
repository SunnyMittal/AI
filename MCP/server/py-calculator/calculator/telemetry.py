"""OpenTelemetry instrumentation for the calculator MCP server."""
import os
import logging
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter


def initialize_telemetry(service_name: str | None = None, version: str | None = None) -> None:
    """Initialize OpenTelemetry with Phoenix exporter."""
    endpoint = os.getenv("PHOENIX_ENDPOINT", "http://localhost:6006/v1/traces")

    # Read service name from environment variables with fallback
    if service_name is None:
        service_name = os.getenv("PHOENIX_PROJECT_NAME") or os.getenv("OTEL_SERVICE_NAME", "py-calculator")

    # Read version from environment variable with fallback
    if version is None:
        version = os.getenv("SERVICE_VERSION", "0.1.0")

    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: version,
        "mcp.protocol_version": "2025-03-26",
    })

    # Initialize tracing
    provider = TracerProvider(resource=resource)

    # Add project name as header for Phoenix
    headers = {}
    project_name = os.getenv("PHOENIX_PROJECT_NAME")
    if project_name:
        headers["x-project-name"] = project_name

    exporter = OTLPSpanExporter(endpoint=endpoint, headers=headers)
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)


def initialize_metrics(service_name: str | None = None, version: str | None = None) -> None:
    """Initialize OpenTelemetry metrics.

    Note: Metrics may not be supported by all Phoenix versions.
    If metrics export fails, it will be logged but won't prevent tracing from working.
    """
    # Check if metrics are explicitly disabled
    if os.getenv("PHOENIX_METRICS_ENABLED", "true").lower() == "false":
        return

    endpoint = os.getenv("PHOENIX_METRICS_ENDPOINT", "http://localhost:6006/v1/metrics")

    # Read service name from environment variables with fallback
    if service_name is None:
        service_name = os.getenv("PHOENIX_PROJECT_NAME") or os.getenv("OTEL_SERVICE_NAME", "py-calculator")

    # Read version from environment variable with fallback
    if version is None:
        version = os.getenv("SERVICE_VERSION", "0.1.0")

    try:
        resource = Resource.create({
            SERVICE_NAME: service_name,
            SERVICE_VERSION: version,
        })

        # Add project name as header for Phoenix
        headers = {}
        project_name = os.getenv("PHOENIX_PROJECT_NAME")
        if project_name:
            headers["x-project-name"] = project_name

        exporter = OTLPMetricExporter(endpoint=endpoint, headers=headers)
        reader = PeriodicExportingMetricReader(exporter)
        provider = MeterProvider(resource=resource, metric_readers=[reader])

        metrics.set_meter_provider(provider)
    except Exception as e:
        # Metrics initialization failed, but this shouldn't prevent tracing
        import logging
        logging.getLogger(__name__).warning(
            f"Failed to initialize metrics (this is non-critical): {e}"
        )


def get_tracer(name: str = "py-calculator"):
    """Get a tracer instance."""
    return trace.get_tracer(name)


def get_meter(name: str = "py-calculator"):
    """Get a meter instance."""
    return metrics.get_meter(name)


class TraceContextFilter(logging.Filter):
    """Add trace context to log records."""

    def filter(self, record):
        span = trace.get_current_span()
        if span.is_recording():
            ctx = span.get_span_context()
            record.trace_id = format(ctx.trace_id, '032x')
            record.span_id = format(ctx.span_id, '016x')
        else:
            record.trace_id = "0" * 32
            record.span_id = "0" * 16
        return True


def configure_logging():
    """Configure logging with trace context.

    This adds trace_id and span_id attributes to all log records.
    These attributes can be used in custom log formatters if desired.
    """
    # Add the trace context filter to the root logger
    logger = logging.getLogger()

    # Only add the filter if it's not already present
    if not any(isinstance(f, TraceContextFilter) for f in logger.filters):
        logger.addFilter(TraceContextFilter())

    # Note: We don't modify existing formatters to avoid breaking existing logging setup.
    # The trace_id and span_id attributes are available in the log record for custom use.
    # To use them in your log format, add %(trace_id)s and %(span_id)s to your formatter.


# Initialize metrics instruments
def create_metrics():
    """Create and return metric instruments."""
    meter = get_meter("py-calculator")

    return {
        "request_counter": meter.create_counter(
            "mcp.requests.total",
            description="Total MCP requests"
        ),
        "request_duration": meter.create_histogram(
            "mcp.requests.duration",
            description="Request duration in ms",
            unit="ms"
        ),
        "tool_call_counter": meter.create_counter(
            "mcp.tools.calls",
            description="Tool invocations"
        ),
        "tool_error_counter": meter.create_counter(
            "mcp.tools.errors",
            description="Tool errors"
        ),
    }
