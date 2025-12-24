package telemetry

import (
	"context"
	"fmt"
	"net/http"
	"strings"
	"time"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
	"go.opentelemetry.io/otel/propagation"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.24.0"
	"go.opentelemetry.io/otel/trace"
)

// Config holds telemetry configuration
type Config struct {
	ServiceName     string
	ServiceVersion  string
	PhoenixEndpoint string
	ProjectName     string
}

// LoadConfig creates telemetry configuration from app config
func LoadConfig(serviceName, version, endpoint, projectName string) Config {
	// Remove trailing slash if present
	endpoint = strings.TrimSuffix(endpoint, "/")

	return Config{
		ServiceName:     serviceName,
		ServiceVersion:  version,
		PhoenixEndpoint: endpoint,
		ProjectName:     projectName,
	}
}

// ensureProjectExists verifies Phoenix is reachable and the project will be auto-created
// Phoenix automatically creates projects when it receives traces with the x-project-name header
func ensureProjectExists(ctx context.Context, phoenixURL, projectName string) error {
	if projectName == "" {
		return nil // No project name specified, skip check
	}

	// Get base URL (remove /v1/traces if present)
	baseURL := strings.TrimSuffix(phoenixURL, "/v1/traces")
	baseURL = strings.TrimSuffix(baseURL, "/")

	client := &http.Client{
		Timeout: 5 * time.Second,
	}

	// Health check - verify Phoenix is running
	// Try the root endpoint which should return the Phoenix UI
	healthURL := baseURL
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, healthURL, nil)
	if err != nil {
		return fmt.Errorf("failed to create health check request: %w", err)
	}

	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("Phoenix not reachable at %s (ensure Phoenix is running): %w", baseURL, err)
	}
	defer resp.Body.Close()

	// If we get any response (200, 404, etc.), Phoenix is running
	// The project will be auto-created when the first trace arrives
	if resp.StatusCode >= 200 && resp.StatusCode < 500 {
		return nil
	}

	return fmt.Errorf("Phoenix health check failed with status: %d", resp.StatusCode)
}

// Initialize sets up OpenTelemetry with Phoenix/OTLP exporter
// Returns a cleanup function that should be called on shutdown
func Initialize(ctx context.Context, cfg Config) (func(context.Context) error, error) {
	// Ensure Phoenix project exists before initializing telemetry
	if err := ensureProjectExists(ctx, cfg.PhoenixEndpoint, cfg.ProjectName); err != nil {
		// Log warning but continue - Phoenix might not be running yet
		// The error will be visible in logs via the caller
		return nil, fmt.Errorf("Phoenix project check failed: %w", err)
	}

	// Parse endpoint to get host (remove protocol and path)
	endpoint := cfg.PhoenixEndpoint
	endpoint = strings.TrimPrefix(endpoint, "http://")
	endpoint = strings.TrimPrefix(endpoint, "https://")

	// Create OTLP HTTP exporter with Phoenix project header
	headers := map[string]string{}
	if cfg.ProjectName != "" {
		headers["x-project-name"] = cfg.ProjectName
	}

	exporter, err := otlptracehttp.New(ctx,
		otlptracehttp.WithEndpoint(endpoint),
		otlptracehttp.WithURLPath("/v1/traces"),
		otlptracehttp.WithInsecure(),
		otlptracehttp.WithHeaders(headers),
	)
	if err != nil {
		return nil, err
	}

	// Create resource with service information
	res, err := resource.New(ctx,
		resource.WithAttributes(
			semconv.ServiceName(cfg.ServiceName),
			semconv.ServiceVersion(cfg.ServiceVersion),
			attribute.String("mcp.protocol_version", "2025-03-26"),
			attribute.String("phoenix.project", cfg.ProjectName),
		),
	)
	if err != nil {
		return nil, err
	}

	// Create trace provider
	tp := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(exporter),
		sdktrace.WithResource(res),
		sdktrace.WithSampler(sdktrace.AlwaysSample()),
	)

	// Set global trace provider
	otel.SetTracerProvider(tp)

	// Set global propagator for trace context
	otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
		propagation.TraceContext{},
		propagation.Baggage{},
	))

	// Return cleanup function
	return tp.Shutdown, nil
}

// Tracer returns the global tracer for the MCP server
func Tracer(name string) trace.Tracer {
	return otel.Tracer(name)
}
