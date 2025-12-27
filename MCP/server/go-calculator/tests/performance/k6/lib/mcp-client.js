import http from 'k6/http';
import { check } from 'k6';

// MCP Protocol constants
const JSONRPC_VERSION = '2.0';
const PROTOCOL_VERSION = '2025-03-26';
// Note: Go canonicalizes HTTP headers to Title-Case, so we use both forms
const HEADER_SESSION_ID = 'Mcp-Session-Id'; // For response headers (Go canonicalizes)

// Server configuration
const BASE_URL = __ENV.SERVER_URL || 'http://localhost:8200';
const MCP_ENDPOINT = `${BASE_URL}/mcp`;

// Global request ID counter (per VU)
let requestId = 0;

/**
 * Parse SSE (Server-Sent Events) response format
 * SSE format: "event: message\ndata: {...}\n\n"
 */
export function parseSSEResponse(body) {
  const lines = body.split('\n');
  let eventData = null;

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const jsonStr = line.substring(6).trim();
      if (jsonStr) {
        try {
          eventData = JSON.parse(jsonStr);
        } catch (e) {
          console.error(`Failed to parse SSE data: ${e.message}`);
        }
      }
    }
  }

  return eventData;
}

/**
 * Create a JSON-RPC 2.0 request
 */
function createJSONRPCRequest(method, params = null) {
  requestId++;
  const request = {
    jsonrpc: JSONRPC_VERSION,
    id: requestId,
    method: method,
  };

  if (params !== null) {
    request.params = params;
  }

  return request;
}

/**
 * Initialize a new MCP session
 * Returns the session ID or null on failure
 */
export function initializeSession() {
  const initRequest = createJSONRPCRequest('initialize', {
    protocolVersion: PROTOCOL_VERSION,
    capabilities: {
      experimental: {},
      sampling: {},
    },
    clientInfo: {
      name: 'k6-performance-test',
      version: '1.0.0',
    },
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
  };

  const response = http.post(MCP_ENDPOINT, JSON.stringify(initRequest), params);

  check(response, {
    'initialize: status is 200': (r) => r.status === 200,
    'initialize: has session header': (r) => r.headers[HEADER_SESSION_ID] !== undefined,
  });

  if (response.status === 200) {
    const sessionId = response.headers[HEADER_SESSION_ID];

    // Parse SSE response to verify initialization
    const data = parseSSEResponse(response.body);
    if (data && data.result) {
      return sessionId;
    }
  }

  console.error(`Failed to initialize session: ${response.status} - ${response.body}`);
  return null;
}

/**
 * Call a tool within an existing session
 * Returns the tool call result or null on failure
 */
export function callTool(sessionId, toolName, args = {}) {
  if (!sessionId) {
    console.error('callTool: sessionId is required');
    return null;
  }

  const toolCallRequest = createJSONRPCRequest('tools/call', {
    name: toolName,
    arguments: args,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      [HEADER_SESSION_ID]: sessionId,
    },
  };

  const response = http.post(MCP_ENDPOINT, JSON.stringify(toolCallRequest), params);

  check(response, {
    'tool call: status is 200': (r) => r.status === 200,
    'tool call: response is valid SSE': (r) => r.body.includes('data:'),
  });

  if (response.status === 200) {
    const data = parseSSEResponse(response.body);

    if (data && data.result) {
      // Extract result from MCP tool call response
      // Result format: { content: [{ type: "text", text: "value" }], isError: false }
      if (data.result.content && data.result.content.length > 0) {
        const resultText = data.result.content[0].text;
        return {
          success: !data.result.isError,
          value: resultText,
          raw: data.result,
        };
      }
    } else if (data && data.error) {
      console.error(`Tool call error: ${data.error.message}`);
      return {
        success: false,
        error: data.error,
      };
    }
  }

  console.error(`Tool call failed: ${response.status} - ${response.body}`);
  return null;
}

/**
 * List available tools in a session
 */
export function listTools(sessionId) {
  if (!sessionId) {
    console.error('listTools: sessionId is required');
    return null;
  }

  const listRequest = createJSONRPCRequest('tools/list');

  const params = {
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      [HEADER_SESSION_ID]: sessionId,
    },
  };

  const response = http.post(MCP_ENDPOINT, JSON.stringify(listRequest), params);

  if (response.status === 200) {
    const data = parseSSEResponse(response.body);
    return data ? data.result : null;
  }

  return null;
}

/**
 * Delete/terminate an MCP session
 */
export function deleteSession(sessionId) {
  if (!sessionId) {
    return false;
  }

  const params = {
    headers: {
      [HEADER_SESSION_ID]: sessionId,
    },
  };

  const response = http.del(MCP_ENDPOINT, null, params);

  check(response, {
    'delete session: status is 200 or 204': (r) => r.status === 200 || r.status === 204,
  });

  return response.status === 200 || response.status === 204;
}

/**
 * Health check endpoint
 */
export function healthCheck() {
  const response = http.get(`${BASE_URL}/health`);
  return response.status === 200;
}

/**
 * Get server metrics
 */
export function getMetrics() {
  const response = http.get(`${BASE_URL}/metrics`);
  if (response.status === 200) {
    try {
      return JSON.parse(response.body);
    } catch (e) {
      console.error(`Failed to parse metrics: ${e.message}`);
    }
  }
  return null;
}

/**
 * Perform a complete MCP interaction: initialize, call tool, cleanup
 * This is a convenience function for simple test scenarios
 */
export function performCalculation(toolName, a, b) {
  const sessionId = initializeSession();
  if (!sessionId) {
    return null;
  }

  const result = callTool(sessionId, toolName, { a, b });
  deleteSession(sessionId);

  return result;
}
