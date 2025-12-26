"""Tests for the telemetry module."""
import pytest
from unittest.mock import patch, MagicMock
from calculator.telemetry import (
    initialize_telemetry,
    initialize_metrics,
    get_tracer,
    get_meter,
    TraceContextFilter,
    create_metrics
)


class TestTelemetryInitialization:
    """Test telemetry initialization functions."""

    @patch('calculator.telemetry.trace.set_tracer_provider')
    @patch('calculator.telemetry.OTLPSpanExporter')
    @patch('calculator.telemetry.TracerProvider')
    def test_initialize_telemetry_default_endpoint(
        self, mock_provider, mock_exporter, mock_set_provider
    ):
        """Test telemetry initialization with default endpoint."""
        initialize_telemetry("test-service", "1.0.0")

        mock_exporter.assert_called_once()
        mock_provider.assert_called_once()
        mock_set_provider.assert_called_once()

    @patch.dict('os.environ', {'PHOENIX_ENDPOINT': 'http://custom:6006/v1/traces'})
    @patch('calculator.telemetry.trace.set_tracer_provider')
    @patch('calculator.telemetry.OTLPSpanExporter')
    @patch('calculator.telemetry.TracerProvider')
    def test_initialize_telemetry_custom_endpoint(
        self, mock_provider, mock_exporter, mock_set_provider
    ):
        """Test telemetry initialization with custom endpoint."""
        initialize_telemetry("test-service", "1.0.0")

        # Verify custom endpoint was used
        call_kwargs = mock_exporter.call_args[1]
        assert 'endpoint' in call_kwargs
        assert call_kwargs['endpoint'] == 'http://custom:6006/v1/traces'

    @patch('calculator.telemetry.metrics.set_meter_provider')
    @patch('calculator.telemetry.OTLPMetricExporter')
    @patch('calculator.telemetry.MeterProvider')
    def test_initialize_metrics(
        self, mock_provider, mock_exporter, mock_set_provider
    ):
        """Test metrics initialization."""
        initialize_metrics("test-service", "1.0.0")

        mock_exporter.assert_called_once()
        mock_provider.assert_called_once()
        mock_set_provider.assert_called_once()


class TestTracerAndMeter:
    """Test tracer and meter getters."""

    @patch('calculator.telemetry.trace.get_tracer')
    def test_get_tracer_default(self, mock_get_tracer):
        """Test getting tracer with default name."""
        get_tracer()
        mock_get_tracer.assert_called_once_with("py-calculator")

    @patch('calculator.telemetry.trace.get_tracer')
    def test_get_tracer_custom(self, mock_get_tracer):
        """Test getting tracer with custom name."""
        get_tracer("custom-name")
        mock_get_tracer.assert_called_once_with("custom-name")

    @patch('calculator.telemetry.metrics.get_meter')
    def test_get_meter_default(self, mock_get_meter):
        """Test getting meter with default name."""
        get_meter()
        mock_get_meter.assert_called_once_with("py-calculator")

    @patch('calculator.telemetry.metrics.get_meter')
    def test_get_meter_custom(self, mock_get_meter):
        """Test getting meter with custom name."""
        get_meter("custom-name")
        mock_get_meter.assert_called_once_with("custom-name")


class TestTraceContextFilter:
    """Test trace context filter for logging."""

    def test_filter_with_active_span(self):
        """Test filter adds trace context when span is recording."""
        filter_instance = TraceContextFilter()
        record = MagicMock()

        # Mock an active span
        mock_span = MagicMock()
        mock_span.is_recording.return_value = True
        mock_ctx = MagicMock()
        mock_ctx.trace_id = 12345
        mock_ctx.span_id = 67890
        mock_span.get_span_context.return_value = mock_ctx

        with patch('calculator.telemetry.trace.get_current_span', return_value=mock_span):
            result = filter_instance.filter(record)

        assert result is True
        assert hasattr(record, 'trace_id')
        assert hasattr(record, 'span_id')

    def test_filter_without_active_span(self):
        """Test filter with no active span."""
        filter_instance = TraceContextFilter()
        record = MagicMock()

        # Mock an inactive span
        mock_span = MagicMock()
        mock_span.is_recording.return_value = False

        with patch('calculator.telemetry.trace.get_current_span', return_value=mock_span):
            result = filter_instance.filter(record)

        assert result is True
        assert record.trace_id == "0" * 32
        assert record.span_id == "0" * 16


class TestMetricsCreation:
    """Test metrics creation."""

    @patch('calculator.telemetry.get_meter')
    def test_create_metrics(self, mock_get_meter):
        """Test creating metrics instruments."""
        mock_meter = MagicMock()
        mock_get_meter.return_value = mock_meter

        # Setup mock return values
        mock_meter.create_counter.return_value = MagicMock()
        mock_meter.create_histogram.return_value = MagicMock()

        metrics = create_metrics()

        # Verify all metrics were created
        assert "request_counter" in metrics
        assert "request_duration" in metrics
        assert "tool_call_counter" in metrics
        assert "tool_error_counter" in metrics

        # Verify create methods were called
        assert mock_meter.create_counter.call_count == 3  # 3 counters
        assert mock_meter.create_histogram.call_count == 1  # 1 histogram
