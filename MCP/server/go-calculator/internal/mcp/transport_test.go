package mcp

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/mcp/go-calculator/internal/logger"
)

func init() {
	// Initialize logger for tests
	_ = logger.Initialize("error", "console")
}

// Helper function to parse SSE response and extract JSON-RPC message
func parseSSEResponse(body string) (*JSONRPCResponse, error) {
	lines := strings.Split(body, "\n")
	for i, line := range lines {
		if strings.HasPrefix(line, "data: ") {
			jsonData := strings.TrimPrefix(line, "data: ")
			var resp JSONRPCResponse
			if err := json.Unmarshal([]byte(jsonData), &resp); err != nil {
				return nil, err
			}
			return &resp, nil
		}
		// Also check if next line after "event: message" contains data
		if strings.HasPrefix(line, "event: message") && i+1 < len(lines) {
			if strings.HasPrefix(lines[i+1], "data: ") {
				jsonData := strings.TrimPrefix(lines[i+1], "data: ")
				var resp JSONRPCResponse
				if err := json.Unmarshal([]byte(jsonData), &resp); err != nil {
					return nil, err
				}
				return &resp, nil
			}
		}
	}
	return nil, fmt.Errorf("no SSE data found in response")
}

func TestTransport_HandleMessage_Initialize(t *testing.T) {
	server := NewServer("test")
	transport := NewTransport(server)

	initReq := JSONRPCRequest{
		JSONRPC: JSONRPCVersion,
		ID:      1,
		Method:  MethodInitialize,
		Params: json.RawMessage(`{
			"protocolVersion": "2024-11-05",
			"capabilities": {},
			"clientInfo": {
				"name": "test-client",
				"version": "1.0.0"
			}
		}`),
	}

	body, _ := json.Marshal(initReq)
	req := httptest.NewRequest(http.MethodPost, "/mcp", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "text/event-stream")

	w := httptest.NewRecorder()
	transport.handleMCPPost(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", w.Code)
	}

	// Check session header is set
	sessionID := w.Header().Get(HeaderMCPSessionID)
	if sessionID == "" {
		t.Error("Expected session ID header to be set")
	}

	resp, err := parseSSEResponse(w.Body.String())
	if err != nil {
		t.Fatalf("Failed to parse SSE response: %v", err)
	}

	if resp.Error != nil {
		t.Errorf("Expected no error, got: %v", resp.Error)
	}

	// Compare IDs as strings since JSON unmarshaling may change types (int -> float64)
	if fmt.Sprintf("%v", resp.ID) != fmt.Sprintf("%v", initReq.ID) {
		t.Errorf("Expected ID %v, got %v", initReq.ID, resp.ID)
	}
}

func TestTransport_HandleMessage_ToolsList(t *testing.T) {
	server := NewServer("test")
	transport := NewTransport(server)

	// First initialize to get session
	initReq := JSONRPCRequest{
		JSONRPC: JSONRPCVersion,
		ID:      1,
		Method:  MethodInitialize,
		Params: json.RawMessage(`{
			"protocolVersion": "2024-11-05",
			"capabilities": {},
			"clientInfo": {"name": "test", "version": "1.0.0"}
		}`),
	}
	body, _ := json.Marshal(initReq)
	req := httptest.NewRequest(http.MethodPost, "/mcp", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "text/event-stream")
	w := httptest.NewRecorder()
	transport.handleMCPPost(w, req)
	sessionID := w.Header().Get(HeaderMCPSessionID)

	// Now test tools/list
	listReq := JSONRPCRequest{
		JSONRPC: JSONRPCVersion,
		ID:      2,
		Method:  MethodToolsList,
	}

	body, _ = json.Marshal(listReq)
	req = httptest.NewRequest(http.MethodPost, "/mcp", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "text/event-stream")
	req.Header.Set(HeaderMCPSessionID, sessionID)

	w = httptest.NewRecorder()
	transport.handleMCPPost(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", w.Code)
	}

	resp, err := parseSSEResponse(w.Body.String())
	if err != nil {
		t.Fatalf("Failed to parse SSE response: %v", err)
	}

	if resp.Error != nil {
		t.Errorf("Expected no error, got: %v", resp.Error)
	}

	// Verify tools are returned
	resultJSON, _ := json.Marshal(resp.Result)
	var result ToolsListResult
	if err := json.Unmarshal(resultJSON, &result); err != nil {
		t.Fatalf("Failed to decode tools list: %v", err)
	}

	if len(result.Tools) != 4 {
		t.Errorf("Expected 4 tools, got %d", len(result.Tools))
	}

	// Verify tool names
	expectedTools := map[string]bool{"add": true, "subtract": true, "multiply": true, "divide": true}
	for _, tool := range result.Tools {
		if !expectedTools[tool.Name] {
			t.Errorf("Unexpected tool: %s", tool.Name)
		}
	}
}

func TestTransport_HandleMessage_ToolsCall_Add(t *testing.T) {
	server := NewServer("test")
	transport := NewTransport(server)

	// First initialize to get session
	initReq := JSONRPCRequest{
		JSONRPC: JSONRPCVersion,
		ID:      1,
		Method:  MethodInitialize,
		Params: json.RawMessage(`{
			"protocolVersion": "2024-11-05",
			"capabilities": {},
			"clientInfo": {"name": "test", "version": "1.0.0"}
		}`),
	}
	body, _ := json.Marshal(initReq)
	req := httptest.NewRequest(http.MethodPost, "/mcp", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "text/event-stream")
	w := httptest.NewRecorder()
	transport.handleMCPPost(w, req)
	sessionID := w.Header().Get(HeaderMCPSessionID)

	// Now test tool call
	callReq := JSONRPCRequest{
		JSONRPC: JSONRPCVersion,
		ID:      3,
		Method:  MethodToolsCall,
		Params: json.RawMessage(`{
			"name": "add",
			"arguments": {
				"a": 5,
				"b": 3
			}
		}`),
	}

	body, _ = json.Marshal(callReq)
	req = httptest.NewRequest(http.MethodPost, "/mcp", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "text/event-stream")
	req.Header.Set(HeaderMCPSessionID, sessionID)

	w = httptest.NewRecorder()
	transport.handleMCPPost(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", w.Code)
	}

	resp, err := parseSSEResponse(w.Body.String())
	if err != nil {
		t.Fatalf("Failed to parse SSE response: %v", err)
	}

	if resp.Error != nil {
		t.Errorf("Expected no error, got: %v", resp.Error)
	}

	resultJSON, _ := json.Marshal(resp.Result)
	var result ToolCallResult
	if err := json.Unmarshal(resultJSON, &result); err != nil {
		t.Fatalf("Failed to decode tool call result: %v", err)
	}

	if result.IsError {
		t.Error("Expected success, got error")
	}

	if len(result.Content) == 0 {
		t.Fatal("Expected content in result")
	}

	if result.Content[0].Text != "8" {
		t.Errorf("Expected result 8, got %s", result.Content[0].Text)
	}
}

func TestTransport_HandleMessage_ToolsCall_Divide(t *testing.T) {
	server := NewServer("test")
	transport := NewTransport(server)

	// First initialize to get session
	initReq := JSONRPCRequest{
		JSONRPC: JSONRPCVersion,
		ID:      1,
		Method:  MethodInitialize,
		Params: json.RawMessage(`{
			"protocolVersion": "2024-11-05",
			"capabilities": {},
			"clientInfo": {"name": "test", "version": "1.0.0"}
		}`),
	}
	body, _ := json.Marshal(initReq)
	req := httptest.NewRequest(http.MethodPost, "/mcp", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "text/event-stream")
	w := httptest.NewRecorder()
	transport.handleMCPPost(w, req)
	sessionID := w.Header().Get(HeaderMCPSessionID)

	tests := []struct {
		name        string
		a           float64
		b           float64
		expectError bool
		expected    string
	}{
		{"valid division", 10, 2, false, "5"},
		{"division by zero", 10, 0, true, ""},
		{"negative division", -10, 2, false, "-5"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			callReq := JSONRPCRequest{
				JSONRPC: JSONRPCVersion,
				ID:      4,
				Method:  MethodToolsCall,
				Params: json.RawMessage(
					`{"name": "divide", "arguments": {"a": ` +
						json.Number(fmt.Sprintf("%f", tt.a)).String() +
						`, "b": ` +
						json.Number(fmt.Sprintf("%f", tt.b)).String() +
						`}}`,
				),
			}

			body, _ := json.Marshal(callReq)
			req := httptest.NewRequest(http.MethodPost, "/mcp", bytes.NewReader(body))
			req.Header.Set("Content-Type", "application/json")
			req.Header.Set("Accept", "text/event-stream")
			req.Header.Set(HeaderMCPSessionID, sessionID)

			w := httptest.NewRecorder()
			transport.handleMCPPost(w, req)

			resp, _ := parseSSEResponse(w.Body.String())

			resultJSON, _ := json.Marshal(resp.Result)
			var result ToolCallResult
			json.Unmarshal(resultJSON, &result)

			if tt.expectError && !result.IsError {
				t.Error("Expected error result")
			}

			if !tt.expectError && result.IsError {
				t.Errorf("Expected success, got error: %s", result.Content[0].Text)
			}

			if !tt.expectError && result.Content[0].Text != tt.expected {
				t.Errorf("Expected %s, got %s", tt.expected, result.Content[0].Text)
			}
		})
	}
}

func TestTransport_HandleMessage_InvalidJSON(t *testing.T) {
	server := NewServer("test")
	transport := NewTransport(server)

	req := httptest.NewRequest(http.MethodPost, "/mcp", bytes.NewReader([]byte("invalid json")))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "text/event-stream")

	w := httptest.NewRecorder()
	transport.handleMCPPost(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", w.Code)
	}

	resp, err := parseSSEResponse(w.Body.String())
	if err != nil {
		t.Fatalf("Failed to parse SSE response: %v", err)
	}

	if resp.Error == nil {
		t.Error("Expected error response for invalid JSON")
	}

	if resp.Error.Code != ParseError {
		t.Errorf("Expected parse error code %d, got %d", ParseError, resp.Error.Code)
	}
}

func TestTransport_HandleMessage_MethodNotFound(t *testing.T) {
	server := NewServer("test")
	transport := NewTransport(server)

	// First initialize to get session
	initReq := JSONRPCRequest{
		JSONRPC: JSONRPCVersion,
		ID:      1,
		Method:  MethodInitialize,
		Params: json.RawMessage(`{
			"protocolVersion": "2024-11-05",
			"capabilities": {},
			"clientInfo": {"name": "test", "version": "1.0.0"}
		}`),
	}
	body, _ := json.Marshal(initReq)
	req := httptest.NewRequest(http.MethodPost, "/mcp", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "text/event-stream")
	w := httptest.NewRecorder()
	transport.handleMCPPost(w, req)
	sessionID := w.Header().Get(HeaderMCPSessionID)

	callReq := JSONRPCRequest{
		JSONRPC: JSONRPCVersion,
		ID:      5,
		Method:  "unknown_method",
	}

	body, _ = json.Marshal(callReq)
	req = httptest.NewRequest(http.MethodPost, "/mcp", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "text/event-stream")
	req.Header.Set(HeaderMCPSessionID, sessionID)

	w = httptest.NewRecorder()
	transport.handleMCPPost(w, req)

	resp, _ := parseSSEResponse(w.Body.String())

	if resp.Error == nil {
		t.Error("Expected error response for unknown method")
	}

	if resp.Error.Code != MethodNotFound {
		t.Errorf("Expected method not found code %d, got %d", MethodNotFound, resp.Error.Code)
	}
}

func TestTransport_HealthEndpoint(t *testing.T) {
	server := NewServer("test")
	transport := NewTransport(server)

	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	w := httptest.NewRecorder()

	transport.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", w.Code)
	}

	var health map[string]interface{}
	if err := json.NewDecoder(w.Body).Decode(&health); err != nil {
		t.Fatalf("Failed to decode health response: %v", err)
	}

	if health["status"] != "healthy" {
		t.Errorf("Expected healthy status, got %v", health["status"])
	}
}

func TestTransport_MetricsEndpoint(t *testing.T) {
	server := NewServer("test")
	transport := NewTransport(server)

	req := httptest.NewRequest(http.MethodGet, "/metrics", nil)
	w := httptest.NewRecorder()

	transport.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", w.Code)
	}

	var metrics map[string]interface{}
	if err := json.NewDecoder(w.Body).Decode(&metrics); err != nil {
		t.Fatalf("Failed to decode metrics response: %v", err)
	}

	if _, exists := metrics["active_connections"]; !exists {
		t.Error("Expected active_connections in metrics")
	}
}

func TestTransport_ContextCancellation(t *testing.T) {
	server := NewServer("test")
	transport := NewTransport(server)

	// First initialize to get session
	initReq := JSONRPCRequest{
		JSONRPC: JSONRPCVersion,
		ID:      1,
		Method:  MethodInitialize,
		Params: json.RawMessage(`{
			"protocolVersion": "2024-11-05",
			"capabilities": {},
			"clientInfo": {"name": "test", "version": "1.0.0"}
		}`),
	}
	body, _ := json.Marshal(initReq)
	req := httptest.NewRequest(http.MethodPost, "/mcp", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "text/event-stream")
	w := httptest.NewRecorder()
	transport.handleMCPPost(w, req)
	sessionID := w.Header().Get(HeaderMCPSessionID)

	ctx, cancel := context.WithCancel(context.Background())
	cancel() // Cancel immediately

	callReq := JSONRPCRequest{
		JSONRPC: JSONRPCVersion,
		ID:      6,
		Method:  MethodToolsCall,
		Params: json.RawMessage(`{
			"name": "add",
			"arguments": {"a": 1, "b": 2}
		}`),
	}

	body, _ = json.Marshal(callReq)
	req = httptest.NewRequest(http.MethodPost, "/mcp", bytes.NewReader(body))
	req = req.WithContext(ctx)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "text/event-stream")
	req.Header.Set(HeaderMCPSessionID, sessionID)

	w = httptest.NewRecorder()
	transport.handleMCPPost(w, req)

	// The request should still complete, but context cancellation is checked
	if w.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", w.Code)
	}
}

// Benchmark tests
func BenchmarkTransport_ToolCall(b *testing.B) {
	server := NewServer("test")
	transport := NewTransport(server)

	// First initialize to get session
	initReq := JSONRPCRequest{
		JSONRPC: JSONRPCVersion,
		ID:      1,
		Method:  MethodInitialize,
		Params: json.RawMessage(`{
			"protocolVersion": "2024-11-05",
			"capabilities": {},
			"clientInfo": {"name": "test", "version": "1.0.0"}
		}`),
	}
	body, _ := json.Marshal(initReq)
	req := httptest.NewRequest(http.MethodPost, "/mcp", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "text/event-stream")
	w := httptest.NewRecorder()
	transport.handleMCPPost(w, req)
	sessionID := w.Header().Get(HeaderMCPSessionID)

	callReq := JSONRPCRequest{
		JSONRPC: JSONRPCVersion,
		ID:      2,
		Method:  MethodToolsCall,
		Params: json.RawMessage(`{
			"name": "add",
			"arguments": {"a": 5, "b": 3}
		}`),
	}

	body, _ = json.Marshal(callReq)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		req := httptest.NewRequest(http.MethodPost, "/mcp", bytes.NewReader(body))
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("Accept", "text/event-stream")
		req.Header.Set(HeaderMCPSessionID, sessionID)
		w := httptest.NewRecorder()
		transport.handleMCPPost(w, req)
	}
}
