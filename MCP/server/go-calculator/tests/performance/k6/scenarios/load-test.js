import { check, sleep } from 'k6';
import { Trend, Rate, Counter } from 'k6/metrics';
import { initializeSession, callTool, deleteSession } from '../lib/mcp-client.js';
import { selectRandomOperation, generateOperationData, validateResult, getExpectedResult } from '../lib/test-data.js';
import { loadThresholds } from '../lib/thresholds.js';

// Custom metrics
const sessionCreationTime = new Trend('mcp_session_creation_ms');
const sessionReuseRate = new Rate('mcp_session_reuse_rate');
const toolCallDuration = new Trend('mcp_tool_call_duration_ms');
const toolCallErrors = new Rate('mcp_tool_call_errors');

// Per-operation metrics
const addDuration = new Trend('operation_add_ms');
const subtractDuration = new Trend('operation_subtract_ms');
const multiplyDuration = new Trend('operation_multiply_ms');
const divideDuration = new Trend('operation_divide_ms');

// Result validation
const resultValidation = new Rate('result_validation_passed');
const divideByZeroErrors = new Counter('operation_divide_by_zero');

// Test options
export const options = {
  scenarios: {
    load_pattern: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        // Ramp up to 50 VUs over 1 minute
        { duration: '1m', target: 50 },
        // Sustain 50 VUs for 5 minutes
        { duration: '5m', target: 50 },
        // Ramp up to 100 VUs over 1 minute
        { duration: '1m', target: 100 },
        // Sustain 100 VUs for 5 minutes
        { duration: '5m', target: 100 },
        // Ramp down to 0 over 1 minute
        { duration: '1m', target: 0 },
      ],
      gracefulRampDown: '30s',
    },
  },
  thresholds: loadThresholds,
};

// VU-level session (shared across iterations for same VU)
let sessionId = null;
let iterationCount = 0;

// Setup function (runs once per VU at start)
export function setup() {
  console.log('Load test starting...');
  console.log('Test will run for approximately 14 minutes');
  return { startTime: Date.now() };
}

// Main test function (runs repeatedly per VU)
export default function (data) {
  // Create session on first iteration or if session was lost
  if (!sessionId) {
    const sessionStart = Date.now();
    sessionId = initializeSession();
    const sessionEnd = Date.now();

    if (!sessionId) {
      console.error('Failed to initialize session');
      return;
    }

    sessionCreationTime.add(sessionEnd - sessionStart);
    sessionReuseRate.add(0); // New session
  } else {
    sessionReuseRate.add(1); // Reusing session
  }

  iterationCount++;

  // Select random operation (40% add, 30% subtract, 20% multiply, 10% divide)
  const operation = selectRandomOperation();

  // Generate test data for the operation
  const testData = generateOperationData(operation);
  const { a, b } = testData;

  // Call the tool and measure duration
  const toolCallStart = Date.now();
  const result = callTool(sessionId, operation, { a, b });
  const toolCallEnd = Date.now();
  const duration = toolCallEnd - toolCallStart;

  // Record metrics
  toolCallDuration.add(duration);

  // Record per-operation duration
  switch (operation) {
    case 'add':
      addDuration.add(duration);
      break;
    case 'subtract':
      subtractDuration.add(duration);
      break;
    case 'multiply':
      multiplyDuration.add(duration);
      break;
    case 'divide':
      divideDuration.add(duration);
      break;
  }

  // Validate result
  if (result && result.success) {
    const expected = getExpectedResult(operation, a, b);
    const isValid = validateResult(result.value, expected);

    resultValidation.add(isValid);

    if (!isValid) {
      console.warn(`Validation failed for ${operation}(${a}, ${b}): got ${result.value}, expected ${expected}`);
    }
  } else if (result && result.error) {
    // Check if it's expected error (division by zero)
    if (operation === 'divide' && b === 0) {
      divideByZeroErrors.add(1);
    } else {
      toolCallErrors.add(1);
      console.error(`Tool call error: ${JSON.stringify(result.error)}`);
    }
  } else {
    toolCallErrors.add(1);
    console.error(`Tool call failed for ${operation}(${a}, ${b})`);
  }

  // Small sleep between requests to simulate realistic usage
  sleep(0.1);
}

// Teardown function (runs once per VU at end)
export function teardown(data) {
  // Clean up session
  if (sessionId) {
    deleteSession(sessionId);
  }

  const endTime = Date.now();
  const duration = (endTime - data.startTime) / 1000;
  console.log(`Load test completed in ${duration.toFixed(2)} seconds`);
}
