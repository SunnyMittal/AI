import { check, sleep } from 'k6';
import { Trend, Rate, Counter } from 'k6/metrics';
import { initializeSession, callTool, deleteSession, getMetrics } from '../lib/mcp-client.js';
import { selectRandomOperation, generateOperationData } from '../lib/test-data.js';
import { enduranceThresholds } from '../lib/thresholds.js';

// Custom metrics
const toolCallDuration = new Trend('mcp_tool_call_duration_ms');
const toolCallErrors = new Rate('mcp_tool_call_errors');
const memoryUsageMB = new Trend('server_memory_mb');
const sessionLifetime = new Trend('session_lifetime_seconds');

// Test options - long-running stability test
export const options = {
  scenarios: {
    endurance_pattern: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        // Ramp up slowly to 50 VUs over 5 minutes
        { duration: '5m', target: 50 },
        // Sustain 50 VUs for 2 hours
        { duration: '2h', target: 50 },
        // Ramp down over 5 minutes
        { duration: '5m', target: 0 },
      ],
      gracefulRampDown: '1m',
    },
  },
  thresholds: enduranceThresholds,
};

let sessionId = null;
let sessionStartTime = null;

// Setup function
export function setup() {
  console.log('Endurance test starting...');
  console.log('Running for 2+ hours to detect memory leaks and degradation...');
  console.log('Monitor server memory usage during test');

  return { startTime: Date.now() };
}

// Main test function
export default function (data) {
  // Create session on first iteration
  if (!sessionId) {
    sessionId = initializeSession();
    sessionStartTime = Date.now();

    if (!sessionId) {
      console.error('Failed to initialize session');
      return;
    }
  }

  // Select random operation
  const operation = selectRandomOperation();
  const { a, b } = generateOperationData(operation);

  // Call tool
  const start = Date.now();
  const result = callTool(sessionId, operation, { a, b });
  const duration = Date.now() - start;

  toolCallDuration.add(duration);

  // Check for errors
  if (!result || !result.success) {
    toolCallErrors.add(1);
  }

  // Periodically check server metrics (every 100 iterations)
  if (__ITER % 100 === 0) {
    const metrics = getMetrics();
    if (metrics) {
      // Track memory usage over time
      if (metrics.memory_mb !== undefined) {
        memoryUsageMB.add(metrics.memory_mb);
      }

      // Log progress every 10 minutes
      const elapsed = (Date.now() - data.startTime) / 1000 / 60;
      if (Math.floor(elapsed) % 10 === 0 && __ITER % 1000 === 0) {
        console.log(`Progress: ${elapsed.toFixed(0)} minutes elapsed, VU ${__VU}, Iteration ${__ITER}`);
      }
    }
  }

  // Realistic sleep between requests
  sleep(0.5);
}

// Teardown function
export function teardown(data) {
  if (sessionId) {
    // Calculate session lifetime
    const lifetime = (Date.now() - sessionStartTime) / 1000;
    sessionLifetime.add(lifetime);

    deleteSession(sessionId);
  }

  const endTime = Date.now();
  const duration = (endTime - data.startTime) / 1000 / 60;
  console.log(`Endurance test completed in ${duration.toFixed(2)} minutes`);

  console.log('=== Endurance Test Results ===');
  console.log('Check memory trends for leaks');
  console.log('Check response time trends for degradation');
  console.log('Review error patterns over time');
}
