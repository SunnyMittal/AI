package mcp

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"sync"
	"time"

	"github.com/mcp/go-calculator/internal/logger"
	"go.uber.org/zap"
)

// Transport handles HTTP/SSE communication for MCP
type Transport struct {
	server      *Server
	mu          sync.RWMutex
	connections map[string]*sseConnection
}

// sseConnection represents a Server-Sent Events connection
type sseConnection struct {
	id      string
	writer  http.ResponseWriter
	flusher http.Flusher
	done    chan struct{}
	mu      sync.Mutex
}

// NewTransport creates a new HTTP transport
func NewTransport(server *Server) *Transport {
	return &Transport{
		server:      server,
		connections: make(map[string]*sseConnection),
	}
}

// ServeHTTP implements the http.Handler interface
func (t *Transport) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	// Add CORS headers for browser compatibility
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Accept")

	// Handle preflight requests
	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusOK)
		return
	}

	// Route based on path
	switch r.URL.Path {
	case "/mcp/v1/messages":
		if r.Method == http.MethodPost {
			t.handleMessage(w, r)
		} else {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		}
	case "/mcp/v1/sse":
		if r.Method == http.MethodGet {
			t.handleSSE(w, r)
		} else {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		}
	case "/health":
		t.handleHealth(w, r)
	case "/metrics":
		t.handleMetrics(w, r)
	default:
		http.NotFound(w, r)
	}
}

// handleMessage processes JSON-RPC messages
func (t *Transport) handleMessage(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	// Set request timeout from context
	if deadline, ok := ctx.Deadline(); ok {
		logger.Debug("request has deadline",
			zap.Time("deadline", deadline),
			zap.Duration("remaining", time.Until(deadline)),
		)
	}

	// Read and validate request body
	body, err := io.ReadAll(io.LimitReader(r.Body, 1<<20)) // 1MB limit
	if err != nil {
		logger.Error("failed to read request body", zap.Error(err))
		http.Error(w, "Failed to read request", http.StatusBadRequest)
		return
	}
	defer r.Body.Close()

	// Validate JSON
	if !json.Valid(body) {
		logger.Error("invalid JSON in request")
		t.sendError(w, nil, ParseError, "Parse error", "Invalid JSON")
		return
	}

	// Parse JSON-RPC request
	var req JSONRPCRequest
	if err := json.Unmarshal(body, &req); err != nil {
		logger.Error("failed to unmarshal request", zap.Error(err))
		t.sendError(w, nil, ParseError, "Parse error", err.Error())
		return
	}

	// Validate JSON-RPC version
	if req.JSONRPC != JSONRPCVersion {
		logger.Error("invalid JSON-RPC version", zap.String("version", req.JSONRPC))
		t.sendError(w, req.ID, InvalidRequest, "Invalid request", "Invalid JSON-RPC version")
		return
	}

	// Log request details
	logger.Info("received request",
		zap.String("method", req.Method),
		zap.Any("id", req.ID),
		zap.String("remote_addr", r.RemoteAddr),
	)

	// Handle the request
	resp := t.server.HandleRequest(ctx, &req)

	// Send response
	t.sendJSON(w, resp)
}

// handleSSE handles Server-Sent Events connections
func (t *Transport) handleSSE(w http.ResponseWriter, r *http.Request) {
	// Check if streaming is supported
	flusher, ok := w.(http.Flusher)
	if !ok {
		logger.Error("streaming not supported")
		http.Error(w, "Streaming not supported", http.StatusInternalServerError)
		return
	}

	// Set SSE headers
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("X-Accel-Buffering", "no")

	// Generate connection ID
	connID := fmt.Sprintf("conn-%d", time.Now().UnixNano())

	// Create connection
	conn := &sseConnection{
		id:      connID,
		writer:  w,
		flusher: flusher,
		done:    make(chan struct{}),
	}

	// Register connection
	t.mu.Lock()
	t.connections[connID] = conn
	t.mu.Unlock()

	logger.Info("SSE connection established",
		zap.String("connection_id", connID),
		zap.String("remote_addr", r.RemoteAddr),
	)

	// Send initial connection message
	conn.sendEvent("connected", map[string]string{
		"connectionId": connID,
		"timestamp":    time.Now().Format(time.RFC3339),
	})

	// Keep connection alive with heartbeats
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	ctx := r.Context()
	for {
		select {
		case <-ctx.Done():
			logger.Info("SSE connection closed by client", zap.String("connection_id", connID))
			t.removeConnection(connID)
			return
		case <-conn.done:
			logger.Info("SSE connection closed", zap.String("connection_id", connID))
			t.removeConnection(connID)
			return
		case <-ticker.C:
			if err := conn.sendHeartbeat(); err != nil {
				logger.Error("failed to send heartbeat", zap.Error(err))
				t.removeConnection(connID)
				return
			}
		}
	}
}

// handleHealth returns server health status
func (t *Transport) handleHealth(w http.ResponseWriter, r *http.Request) {
	health := map[string]interface{}{
		"status":    "healthy",
		"timestamp": time.Now().Format(time.RFC3339),
		"service":   "go-calculator",
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(health)
}

// handleMetrics returns basic metrics
func (t *Transport) handleMetrics(w http.ResponseWriter, r *http.Request) {
	t.mu.RLock()
	activeConnections := len(t.connections)
	t.mu.RUnlock()

	metrics := map[string]interface{}{
		"active_connections": activeConnections,
		"timestamp":          time.Now().Format(time.RFC3339),
		"uptime_seconds":     time.Since(time.Now()).Seconds(), // This would be calculated from server start time in production
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(metrics)
}

// sendJSON sends a JSON response
func (t *Transport) sendJSON(w http.ResponseWriter, data interface{}) {
	w.Header().Set("Content-Type", "application/json")

	if err := json.NewEncoder(w).Encode(data); err != nil {
		logger.Error("failed to encode response", zap.Error(err))
		http.Error(w, "Internal server error", http.StatusInternalServerError)
	}
}

// sendError sends a JSON-RPC error response
func (t *Transport) sendError(w http.ResponseWriter, id interface{}, code int, message, data string) {
	resp := NewJSONRPCError(id, code, message, data)
	t.sendJSON(w, resp)
}

// removeConnection removes a connection from the map
func (t *Transport) removeConnection(id string) {
	t.mu.Lock()
	defer t.mu.Unlock()

	if conn, exists := t.connections[id]; exists {
		close(conn.done)
		delete(t.connections, id)
		logger.Debug("connection removed", zap.String("connection_id", id))
	}
}

// sendEvent sends an SSE event
func (c *sseConnection) sendEvent(event string, data interface{}) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	jsonData, err := json.Marshal(data)
	if err != nil {
		return fmt.Errorf("failed to marshal event data: %w", err)
	}

	writer := bufio.NewWriter(c.writer)

	// Write event type
	if event != "" {
		fmt.Fprintf(writer, "event: %s\n", event)
	}

	// Write data
	for _, line := range strings.Split(string(jsonData), "\n") {
		fmt.Fprintf(writer, "data: %s\n", line)
	}

	// End of event
	fmt.Fprintf(writer, "\n")

	if err := writer.Flush(); err != nil {
		return fmt.Errorf("failed to flush writer: %w", err)
	}

	c.flusher.Flush()
	return nil
}

// sendHeartbeat sends a heartbeat event
func (c *sseConnection) sendHeartbeat() error {
	return c.sendEvent("heartbeat", map[string]string{
		"timestamp": time.Now().Format(time.RFC3339),
	})
}

// Close closes the SSE connection
func (c *sseConnection) Close() {
	select {
	case <-c.done:
		// Already closed
	default:
		close(c.done)
	}
}
