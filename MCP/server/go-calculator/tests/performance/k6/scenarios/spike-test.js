import { check, sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';
import { initializeSession, callTool, deleteSession } from '../lib/mcp-client.js';
import { selectRandomOperation, generateOperationData } from '../lib/test-data.js';
import { spikeThresholds } from '../lib/thresholds.js';

// Custom metrics
const toolCallDuration = new Trend('mcp_tool_call_duration_ms');
const toolCallErrors = new Rate('mcp_tool_call_errors');
const spikeRecoveryTime = new Trend('spike_recovery_time_ms');

// Test options - sudden traffic spikes
export const options = {
  scenarios: {
    spike_pattern: {
      executor: 'ramping-vus',
      startVUs: 10,
      stages: [
        // Baseline
        { duration: '1m', target: 10 },

        // Spike 1
        { duration: '0s', target: 200 },  // Instant spike
        { duration: '1m', target: 200 },  // Hold spike
        { duration: '0s', target: 10 },   // Instant drop
        { duration: '1m', target: 10 },   // Recovery period

        // Spike 2
        { duration: '0s', target: 200 },
        { duration: '1m', target: 200 },
        { duration: '0s', target: 10 },
        { duration: '1m', target: 10 },

        // Spike 3
        { duration: '0s', target: 200 },
        { duration: '1m', target: 200 },
        { duration: '0s', target: 10 },
        { duration: '1m', target: 10 },

        // Spike 4
        { duration: '0s', target: 200 },
        { duration: '1m', target: 200 },
        { duration: '0s', target: 10 },
        { duration: '1m', target: 10 },

        // Spike 5
        { duration: '0s', target: 200 },
        { duration: '1m', target: 200 },
        { duration: '0s', target: 10 },
        { duration: '1m', target: 10 },

        // Final ramp down
        { duration: '30s', target: 0 },
      ],
      gracefulRampDown: '30s',
    },
  },
  thresholds: spikeThresholds,
};

let sessionId = null;
let lastSpikeStart = null;
let isInSpike = false;

// Setup function
export function setup() {
  console.log('Spike test starting...');
  console.log('Testing recovery from sudden traffic bursts...');
  console.log('5 spike cycles: 10 VUs -> 200 VUs -> 10 VUs');

  return { startTime: Date.now() };
}

// Main test function
export default function (data) {
  // Detect spike transitions
  const currentVUs = __VU;
  if (currentVUs > 100 && !isInSpike) {
    // Entering spike
    isInSpike = true;
    lastSpikeStart = Date.now();
    console.log(`Spike started at VU ${currentVUs}`);
  } else if (currentVUs <= 20 && isInSpike) {
    // Exiting spike
    isInSpike = false;
    if (lastSpikeStart) {
      const recovery = Date.now() - lastSpikeStart;
      spikeRecoveryTime.add(recovery);
      console.log(`Spike ended, recovery time: ${recovery}ms`);
    }
  }

  // Create session on first iteration
  if (!sessionId) {
    sessionId = initializeSession();
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

  // Small sleep
  sleep(0.05);
}

// Teardown function
export function teardown(data) {
  if (sessionId) {
    deleteSession(sessionId);
  }

  const endTime = Date.now();
  const duration = (endTime - data.startTime) / 1000 / 60;
  console.log(`Spike test completed in ${duration.toFixed(2)} minutes`);

  console.log('=== Spike Test Results ===');
  console.log('Check recovery time metrics');
  console.log('Review error rates during spikes');
  console.log('Analyze latency impact of sudden load changes');
}
