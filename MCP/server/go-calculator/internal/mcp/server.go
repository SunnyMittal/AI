package mcp

import (
	"context"
	"encoding/json"
	"fmt"
	"strconv"

	"github.com/mcp/go-calculator/internal/logger"
	"github.com/mcp/go-calculator/pkg/calculator"
	"go.uber.org/zap"
)

// Server represents an MCP server
type Server struct {
	calc    *calculator.Calculator
	tools   []Tool
	version string
}

// NewServer creates a new MCP server instance
func NewServer(version string) *Server {
	s := &Server{
		calc:    calculator.New(),
		version: version,
		tools:   make([]Tool, 0),
	}

	s.registerTools()
	return s
}

// registerTools registers all available calculator tools
func (s *Server) registerTools() {
	s.tools = []Tool{
		{
			Name:        "add",
			Description: "Add two numbers together",
			InputSchema: InputSchema{
				Type: "object",
				Properties: map[string]Property{
					"a": {
						Type:        "number",
						Description: "The first number",
					},
					"b": {
						Type:        "number",
						Description: "The second number",
					},
				},
				Required: []string{"a", "b"},
			},
		},
		{
			Name:        "subtract",
			Description: "Subtract the second number from the first",
			InputSchema: InputSchema{
				Type: "object",
				Properties: map[string]Property{
					"a": {
						Type:        "number",
						Description: "The number to subtract from",
					},
					"b": {
						Type:        "number",
						Description: "The number to subtract",
					},
				},
				Required: []string{"a", "b"},
			},
		},
		{
			Name:        "multiply",
			Description: "Multiply two numbers together",
			InputSchema: InputSchema{
				Type: "object",
				Properties: map[string]Property{
					"a": {
						Type:        "number",
						Description: "The first number",
					},
					"b": {
						Type:        "number",
						Description: "The second number",
					},
				},
				Required: []string{"a", "b"},
			},
		},
		{
			Name:        "divide",
			Description: "Divide the first number by the second",
			InputSchema: InputSchema{
				Type: "object",
				Properties: map[string]Property{
					"a": {
						Type:        "number",
						Description: "The dividend (number to be divided)",
					},
					"b": {
						Type:        "number",
						Description: "The divisor (number to divide by)",
					},
				},
				Required: []string{"a", "b"},
			},
		},
	}
}

// HandleRequest processes an incoming JSON-RPC request
func (s *Server) HandleRequest(ctx context.Context, req *JSONRPCRequest) *JSONRPCResponse {
	logger.Debug("handling request",
		zap.String("method", req.Method),
		zap.Any("id", req.ID),
	)

	switch req.Method {
	case MethodInitialize:
		return s.handleInitialize(req)
	case MethodToolsList:
		return s.handleToolsList(req)
	case MethodToolsCall:
		return s.handleToolsCall(ctx, req)
	default:
		logger.Warn("method not found", zap.String("method", req.Method))
		return NewJSONRPCError(req.ID, MethodNotFound, "Method not found", nil)
	}
}

// handleInitialize processes the initialize request
func (s *Server) handleInitialize(req *JSONRPCRequest) *JSONRPCResponse {
	var params InitializeParams
	if len(req.Params) > 0 {
		if err := json.Unmarshal(req.Params, &params); err != nil {
			logger.Error("failed to parse initialize params", zap.Error(err))
			return NewJSONRPCError(req.ID, InvalidParams, "Invalid parameters", err.Error())
		}
	}

	logger.Info("initializing MCP server",
		zap.String("client", params.ClientInfo.Name),
		zap.String("client_version", params.ClientInfo.Version),
	)

	result := InitializeResult{
		ProtocolVersion: ProtocolVersion,
		Capabilities: ServerCapabilities{
			Tools: &ToolsCapability{
				ListChanged: false,
			},
		},
		ServerInfo: ServerInfo{
			Name:    "go-calculator",
			Version: s.version,
		},
	}

	return NewJSONRPCResponse(req.ID, result)
}

// handleToolsList returns the list of available tools
func (s *Server) handleToolsList(req *JSONRPCRequest) *JSONRPCResponse {
	logger.Debug("listing tools", zap.Int("count", len(s.tools)))

	result := ToolsListResult{
		Tools: s.tools,
	}

	return NewJSONRPCResponse(req.ID, result)
}

// handleToolsCall executes a tool call
func (s *Server) handleToolsCall(ctx context.Context, req *JSONRPCRequest) *JSONRPCResponse {
	var params ToolCallParams
	if err := json.Unmarshal(req.Params, &params); err != nil {
		logger.Error("failed to parse tool call params", zap.Error(err))
		return NewJSONRPCError(req.ID, InvalidParams, "Invalid parameters", err.Error())
	}

	logger.Info("calling tool",
		zap.String("tool", params.Name),
		zap.Any("arguments", params.Arguments),
	)

	// Validate and extract arguments
	a, b, err := s.extractNumbers(params.Arguments)
	if err != nil {
		logger.Error("invalid arguments", zap.Error(err))
		return NewJSONRPCError(req.ID, InvalidParams, err.Error(), nil)
	}

	// Validate numbers
	if err := calculator.ValidateNumbers(a, b); err != nil {
		logger.Error("invalid numbers", zap.Error(err))
		return NewJSONRPCError(req.ID, InvalidParams, err.Error(), nil)
	}

	// Execute the tool
	result, err := s.executeTool(ctx, params.Name, a, b)
	if err != nil {
		logger.Error("tool execution failed",
			zap.String("tool", params.Name),
			zap.Error(err),
		)
		return s.toolErrorResponse(req.ID, err)
	}

	logger.Info("tool execution succeeded",
		zap.String("tool", params.Name),
		zap.Float64("result", result),
	)

	return s.toolSuccessResponse(req.ID, result)
}

// extractNumbers extracts and validates number arguments
func (s *Server) extractNumbers(args map[string]interface{}) (float64, float64, error) {
	aVal, aExists := args["a"]
	bVal, bExists := args["b"]

	if !aExists || !bExists {
		return 0, 0, fmt.Errorf("missing required arguments: 'a' and 'b' are required")
	}

	a, err := toFloat64(aVal)
	if err != nil {
		return 0, 0, fmt.Errorf("invalid argument 'a': %w", err)
	}

	b, err := toFloat64(bVal)
	if err != nil {
		return 0, 0, fmt.Errorf("invalid argument 'b': %w", err)
	}

	return a, b, nil
}

// executeTool executes the specified calculator tool
func (s *Server) executeTool(ctx context.Context, name string, a, b float64) (float64, error) {
	// Check context cancellation
	select {
	case <-ctx.Done():
		return 0, ctx.Err()
	default:
	}

	switch name {
	case "add":
		return s.calc.Add(a, b), nil
	case "subtract":
		return s.calc.Subtract(a, b), nil
	case "multiply":
		return s.calc.Multiply(a, b), nil
	case "divide":
		return s.calc.Divide(a, b)
	default:
		return 0, fmt.Errorf("unknown tool: %s", name)
	}
}

// toolSuccessResponse creates a successful tool call response
func (s *Server) toolSuccessResponse(id interface{}, result float64) *JSONRPCResponse {
	return NewJSONRPCResponse(id, ToolCallResult{
		Content: []Content{
			{
				Type: "text",
				Text: strconv.FormatFloat(result, 'f', -1, 64),
			},
		},
		IsError: false,
	})
}

// toolErrorResponse creates an error tool call response
func (s *Server) toolErrorResponse(id interface{}, err error) *JSONRPCResponse {
	return NewJSONRPCResponse(id, ToolCallResult{
		Content: []Content{
			{
				Type: "text",
				Text: err.Error(),
			},
		},
		IsError: true,
	})
}

// toFloat64 converts various numeric types to float64
func toFloat64(val interface{}) (float64, error) {
	switch v := val.(type) {
	case float64:
		return v, nil
	case float32:
		return float64(v), nil
	case int:
		return float64(v), nil
	case int64:
		return float64(v), nil
	case int32:
		return float64(v), nil
	case string:
		return strconv.ParseFloat(v, 64)
	default:
		return 0, fmt.Errorf("cannot convert %T to float64", val)
	}
}
