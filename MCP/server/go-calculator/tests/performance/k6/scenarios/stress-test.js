import { check, sleep } from 'k6';
import { Trend, Rate, Counter, Gauge } from 'k6/metrics';
import { initializeSession, callTool, deleteSession, getMetrics } from '../lib/mcp-client.js';
import { selectRandomOperation, generateOperationData } from '../lib/test-data.js';
import { stressThresholds } from '../lib/thresholds.js';

// Custom metrics
const toolCallDuration = new Trend('mcp_tool_call_duration_ms');
const toolCallErrors = new Rate('mcp_tool_call_errors');
const rateLimitHits = new Counter('rate_limit_hits');
const currentVUs = new Gauge('current_vus');
const serverActiveConnections = new Gauge('server_active_connections');

// Test options - progressive stress ramp
export const options = {
  scenarios: {
    stress_pattern: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        // Ramp up to 100 VUs over 2 minutes
        { duration: '2m', target: 100 },
        // Hold at 100 VUs for 3 minutes
        { duration: '3m', target: 100 },
        // Ramp up to 200 VUs over 2 minutes
        { duration: '2m', target: 200 },
        // Hold at 200 VUs for 3 minutes
        { duration: '3m', target: 200 },
        // Ramp up to 400 VUs over 2 minutes
        { duration: '2m', target: 400 },
        // Hold at 400 VUs for 3 minutes
        { duration: '3m', target: 400 },
        // Ramp up to 800 VUs over 2 minutes
        { duration: '2m', target: 800 },
        // Hold at 800 VUs for 3 minutes
        { duration: '3m', target: 800 },
        // Ramp down to 0
        { duration: '2m', target: 0 },
      ],
      gracefulRampDown: '30s',
    },
  },
  thresholds: stressThresholds,
};

let sessionId = null;

// Setup function
export function setup() {
  console.log('Stress test starting...');
  console.log('Finding system breaking points...');
  console.log('Test will ramp up to 800 VUs over ~25 minutes');

  return { startTime: Date.now() };
}

// Main test function
export default function (data) {
  // Create session on first iteration
  if (!sessionId) {
    sessionId = initializeSession();
    if (!sessionId) {
      console.error('Failed to initialize session');
      return;
    }
  }

  // Track current VUs
  currentVUs.add(__VU);

  // Select random operation
  const operation = selectRandomOperation();
  const { a, b } = generateOperationData(operation);

  // Call tool and measure
  const start = Date.now();
  const result = callTool(sessionId, operation, { a, b });
  const duration = Date.now() - start;

  toolCallDuration.add(duration);

  // Check for errors
  if (!result || !result.success) {
    toolCallErrors.add(1);

    // Check if it's a rate limit error (HTTP 429)
    if (result && result.error && result.error.code === -32603) {
      rateLimitHits.add(1);
    }
  }

  // Periodically check server metrics
  if (__ITER % 50 === 0) {
    const metrics = getMetrics();
    if (metrics && metrics.active_connections !== undefined) {
      serverActiveConnections.add(metrics.active_connections);
    }
  }

  // Aggressive request pattern (no sleep) to stress the server
  // This simulates maximum load
}

// Teardown function
export function teardown(data) {
  if (sessionId) {
    deleteSession(sessionId);
  }

  const endTime = Date.now();
  const duration = (endTime - data.startTime) / 1000 / 60;
  console.log(`Stress test completed in ${duration.toFixed(2)} minutes`);

  // Report findings
  console.log('=== Stress Test Results ===');
  console.log(`Maximum VUs reached: ${currentVUs}`);
  console.log('Check metrics for breaking point identification');
}
