package mcp

import (
	"bufio"
	"crypto/rand"
	"encoding/hex"
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

// session represents an MCP session
type session struct {
	id        string
	createdAt time.Time
	server    *Server
}

// Transport handles HTTP/SSE communication for MCP
type Transport struct {
	server      *Server
	mu          sync.RWMutex
	sessions    map[string]*session
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
		sessions:    make(map[string]*session),
		connections: make(map[string]*sseConnection),
	}
}

// generateSessionID generates a new unique session ID (32 hex characters like FastMCP)
func generateSessionID() string {
	bytes := make([]byte, 16)
	rand.Read(bytes)
	return hex.EncodeToString(bytes)
}

// getOrCreateSession gets an existing session or creates a new one
func (t *Transport) getOrCreateSession(sessionID string) (*session, string, bool) {
	t.mu.Lock()
	defer t.mu.Unlock()

	// If session ID provided, look it up
	if sessionID != "" {
		if sess, exists := t.sessions[sessionID]; exists {
			return sess, sessionID, false
		}
		// Invalid session ID
		return nil, "", false
	}

	// Create new session
	newID := generateSessionID()
	sess := &session{
		id:        newID,
		createdAt: time.Now(),
		server:    t.server,
	}
	t.sessions[newID] = sess
	logger.Info("created new MCP session", zap.String("session_id", newID))
	return sess, newID, true
}

// deleteSession removes a session
func (t *Transport) deleteSession(sessionID string) bool {
	t.mu.Lock()
	defer t.mu.Unlock()

	if _, exists := t.sessions[sessionID]; exists {
		delete(t.sessions, sessionID)
		logger.Info("deleted MCP session", zap.String("session_id", sessionID))
		return true
	}
	return false
}

// ServeHTTP implements the http.Handler interface
func (t *Transport) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	// Add CORS headers for browser compatibility
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Accept, "+HeaderMCPSessionID)
	w.Header().Set("Access-Control-Expose-Headers", HeaderMCPSessionID)

	// Handle preflight requests
	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusOK)
		return
	}

	// Route based on path - FastMCP compatible single /mcp endpoint
	switch r.URL.Path {
	case "/mcp":
		switch r.Method {
		case http.MethodPost:
			t.handleMCPPost(w, r)
		case http.MethodGet:
			t.handleMCPGet(w, r)
		case http.MethodDelete:
			t.handleMCPDelete(w, r)
		default:
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

// handleMCPPost handles POST requests to /mcp (JSON-RPC messages)
func (t *Transport) handleMCPPost(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	// Validate Accept header - must include text/event-stream for SSE responses
	accept := r.Header.Get("Accept")
	if !strings.Contains(accept, "text/event-stream") && !strings.Contains(accept, "*/*") {
		logger.Error("missing required Accept header", zap.String("accept", accept))
		http.Error(w, "Accept header must include text/event-stream", http.StatusNotAcceptable)
		return
	}

	// Get session ID from header
	sessionID := r.Header.Get(HeaderMCPSessionID)

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
		t.sendSSEError(w, "", nil, ParseError, "Parse error", "Invalid JSON")
		return
	}

	// Parse JSON-RPC request
	var req JSONRPCRequest
	if err := json.Unmarshal(body, &req); err != nil {
		logger.Error("failed to unmarshal request", zap.Error(err))
		t.sendSSEError(w, "", nil, ParseError, "Parse error", err.Error())
		return
	}

	// Validate JSON-RPC version
	if req.JSONRPC != JSONRPCVersion {
		logger.Error("invalid JSON-RPC version", zap.String("version", req.JSONRPC))
		t.sendSSEError(w, "", req.ID, InvalidRequest, "Invalid request", "Invalid JSON-RPC version")
		return
	}

	// Handle session management
	// For initialize requests, create new session if none provided
	// For other requests, require valid session
	var sess *session
	var newSession bool

	if req.Method == MethodInitialize {
		sess, sessionID, newSession = t.getOrCreateSession(sessionID)
		if sess == nil {
			logger.Error("failed to create session")
			t.sendSSEError(w, "", req.ID, InternalError, "Internal error", "Failed to create session")
			return
		}
	} else {
		// Non-initialize requests require valid session
		if sessionID == "" {
			logger.Error("missing session ID for non-initialize request")
			http.Error(w, "Session ID required", http.StatusBadRequest)
			return
		}
		sess, sessionID, newSession = t.getOrCreateSession(sessionID)
		if sess == nil {
			logger.Error("invalid session ID", zap.String("session_id", sessionID))
			http.Error(w, "Invalid or expired session", http.StatusNotFound)
			return
		}
	}

	// Log request details
	logger.Info("received request",
		zap.String("method", req.Method),
		zap.Any("id", req.ID),
		zap.String("session_id", sessionID),
		zap.Bool("new_session", newSession),
		zap.String("remote_addr", r.RemoteAddr),
	)

	// Check if this is a notification (no ID means notification - no response expected)
	// Notifications have methods like "notifications/initialized"
	if req.ID == nil || strings.HasPrefix(req.Method, "notifications/") {
		// For notifications, return 202 Accepted with session header but no body
		w.Header().Set(HeaderMCPSessionID, sessionID)
		w.WriteHeader(http.StatusAccepted)
		logger.Debug("notification processed", zap.String("method", req.Method))
		return
	}

	// Handle the request
	resp := t.server.HandleRequest(ctx, &req)

	// Send SSE response with session ID
	t.sendSSEResponse(w, sessionID, resp)
}

// handleMCPGet handles GET requests to /mcp (SSE stream for server-initiated messages)
func (t *Transport) handleMCPGet(w http.ResponseWriter, r *http.Request) {
	// Get session ID from header
	sessionID := r.Header.Get(HeaderMCPSessionID)
	if sessionID == "" {
		http.Error(w, "Session ID required", http.StatusBadRequest)
		return
	}

	// Validate session exists
	t.mu.RLock()
	_, exists := t.sessions[sessionID]
	t.mu.RUnlock()

	if !exists {
		http.Error(w, "Invalid or expired session", http.StatusNotFound)
		return
	}

	// Check if streaming is supported
	flusher, ok := w.(http.Flusher)
	if !ok {
		logger.Error("streaming not supported")
		http.Error(w, "Streaming not supported", http.StatusInternalServerError)
		return
	}

	// Set SSE headers
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache, no-transform")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("X-Accel-Buffering", "no")
	w.Header().Set(HeaderMCPSessionID, sessionID)

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
		zap.String("session_id", sessionID),
		zap.String("remote_addr", r.RemoteAddr),
	)

	// Send initial connection message
	conn.sendEvent("connected", map[string]string{
		"connectionId": connID,
		"sessionId":    sessionID,
		"timestamp":    time.Now().Format(time.RFC3339),
	})

	// Keep connection alive with heartbeats
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	ctx := r.Context()
	for {
		select {
		case <-ctx.Done():
			logger.Info("SSE connection closed by client",
				zap.String("connection_id", connID),
				zap.String("session_id", sessionID),
			)
			t.removeConnection(connID)
			return
		case <-conn.done:
			logger.Info("SSE connection closed",
				zap.String("connection_id", connID),
				zap.String("session_id", sessionID),
			)
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

// handleMCPDelete handles DELETE requests to /mcp (session termination)
func (t *Transport) handleMCPDelete(w http.ResponseWriter, r *http.Request) {
	sessionID := r.Header.Get(HeaderMCPSessionID)
	if sessionID == "" {
		http.Error(w, "Session ID required", http.StatusBadRequest)
		return
	}

	if t.deleteSession(sessionID) {
		w.WriteHeader(http.StatusOK)
		logger.Info("session terminated via DELETE", zap.String("session_id", sessionID))
	} else {
		http.Error(w, "Invalid or expired session", http.StatusNotFound)
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

// sendSSEResponse sends a JSON-RPC response in SSE format (FastMCP compatible)
func (t *Transport) sendSSEResponse(w http.ResponseWriter, sessionID string, data interface{}) {
	// Set SSE headers - must be set before WriteHeader
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache, no-transform")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("X-Accel-Buffering", "no")
	if sessionID != "" {
		w.Header().Set(HeaderMCPSessionID, sessionID)
	}

	// Marshal the response first to check for errors before writing headers
	jsonData, err := json.Marshal(data)
	if err != nil {
		logger.Error("failed to marshal response", zap.Error(err))
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

	// Explicitly write status header to prevent Go from auto-setting Content-Length
	w.WriteHeader(http.StatusOK)

	// Write SSE format: event: message\ndata: {...}\n\n
	fmt.Fprintf(w, "event: message\n")
	fmt.Fprintf(w, "data: %s\n", string(jsonData))
	fmt.Fprintf(w, "\n")

	// Flush the http response to send immediately
	if flusher, ok := w.(http.Flusher); ok {
		flusher.Flush()
	}
}

// sendSSEError sends a JSON-RPC error response in SSE format
func (t *Transport) sendSSEError(w http.ResponseWriter, sessionID string, id interface{}, code int, message, data string) {
	resp := NewJSONRPCError(id, code, message, data)
	t.sendSSEResponse(w, sessionID, resp)
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
