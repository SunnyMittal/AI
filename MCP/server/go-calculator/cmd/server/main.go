package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/mcp/go-calculator/internal/config"
	"github.com/mcp/go-calculator/internal/logger"
	"github.com/mcp/go-calculator/internal/mcp"
	"github.com/mcp/go-calculator/internal/middleware"
	"go.uber.org/zap"
)

const version = "1.0.0"

func main() {
	// Exit with proper code
	os.Exit(run())
}

func run() int {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to load configuration: %v\n", err)
		return 1
	}

	// Initialize logger
	if err := logger.Initialize(cfg.Log.Level, cfg.Log.Encoding); err != nil {
		fmt.Fprintf(os.Stderr, "Failed to initialize logger: %v\n", err)
		return 1
	}
	defer logger.Sync()

	logger.Info("starting go-calculator MCP server",
		zap.String("version", version),
		zap.String("address", cfg.Address()),
		zap.String("log_level", cfg.Log.Level),
	)

	// Create MCP server
	mcpServer := mcp.NewServer(version)
	transport := mcp.NewTransport(mcpServer)

	// Build middleware chain
	handler := middleware.Chain(
		transport,
		middleware.Logging,
		middleware.Recovery,
		middleware.SecurityHeaders,
		middleware.RequestValidator(1<<20), // 1MB max body size
		middleware.RateLimiter(100),        // 100 requests per second
		middleware.Timeout(30*time.Second),
	)

	// Create HTTP server
	server := &http.Server{
		Addr:         cfg.Address(),
		Handler:      handler,
		ReadTimeout:  cfg.Server.ReadTimeout,
		WriteTimeout: cfg.Server.WriteTimeout,
		IdleTimeout:  cfg.Server.IdleTimeout,
		// Disable HTTP/2 for better SSE compatibility with some clients
		// TLSNextProto: make(map[string]func(*http.Server, *tls.Conn, http.Handler)),
	}

	// Start server in a goroutine
	serverErrors := make(chan error, 1)
	go func() {
		logger.Info("HTTP server listening", zap.String("address", server.Addr))
		serverErrors <- server.ListenAndServe()
	}()

	// Setup signal handling for graceful shutdown
	shutdown := make(chan os.Signal, 1)
	signal.Notify(shutdown, os.Interrupt, syscall.SIGTERM, syscall.SIGINT)

	// Wait for shutdown signal or server error
	select {
	case err := <-serverErrors:
		if err != nil && err != http.ErrServerClosed {
			logger.Error("server error", zap.Error(err))
			return 1
		}

	case sig := <-shutdown:
		logger.Info("shutdown signal received",
			zap.String("signal", sig.String()),
		)

		// Create context with timeout for graceful shutdown
		ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
		defer cancel()

		logger.Info("initiating graceful shutdown",
			zap.Duration("timeout", 30*time.Second),
		)

		// Attempt graceful shutdown
		if err := server.Shutdown(ctx); err != nil {
			logger.Error("graceful shutdown failed, forcing close", zap.Error(err))

			// Force close if graceful shutdown fails
			if closeErr := server.Close(); closeErr != nil {
				logger.Error("error forcing server close", zap.Error(closeErr))
			}
			return 1
		}

		logger.Info("server shutdown completed successfully")
	}

	return 0
}
