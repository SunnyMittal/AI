/**
 * Performance thresholds (SLIs/SLOs) for k6 tests
 * These define the acceptable performance criteria for the go-calculator MCP server
 */

/**
 * Load Test Thresholds
 * Used for baseline performance testing under normal/peak load
 */
export const loadThresholds = {
  // HTTP request duration thresholds
  'http_req_duration': [
    'p(95) < 100',     // 95th percentile < 100ms
    'p(99) < 200',     // 99th percentile < 200ms
    'avg < 50',        // Average latency < 50ms
  ],

  // Error rate threshold
  'http_req_failed': [
    'rate < 0.001',    // Less than 0.1% error rate
  ],

  // Throughput threshold
  'http_reqs': [
    'rate > 90',     // Greater than 1000 requests per second
  ],

  // MCP-specific thresholds
  'mcp_tool_call_duration_ms': [
    'p(95) < 50',      // Tool call p95 < 50ms
  ],

  'mcp_session_creation_ms': [
    'p(95) < 100',     // Session creation p95 < 100ms
  ],

  'mcp_tool_call_errors': [
    'rate < 0.001',    // Tool call error rate < 0.1%
  ],
};

/**
 * Stress Test Thresholds
 * More relaxed thresholds for finding breaking points
 */
export const stressThresholds = {
  'http_req_duration': [
    'p(95) < 500',     // Relaxed during stress test
    'p(99) < 1000',    // Allow some degradation
  ],

  'http_req_failed': [
    'rate < 0.01',     // Allow 1% errors during stress
  ],

  // No throughput threshold - we're finding the limit
};

/**
 * Endurance Test Thresholds
 * Focus on stability over time
 */
export const enduranceThresholds = {
  'http_req_duration': [
    'p(95) < 150',     // Allow some degradation over time
    'p(99) < 300',
    'avg < 75',
  ],

  'http_req_failed': [
    'rate < 0.005',    // 0.5% error rate
  ],

  // No throughput threshold - focus on stability
};

/**
 * Spike Test Thresholds
 * Test recovery from sudden load
 */
export const spikeThresholds = {
  'http_req_duration': [
    'p(95) < 200',     // Allow higher latency during spikes
    'p(99) < 500',
  ],

  'http_req_failed': [
    'rate < 0.01',     // Allow 1% errors during spike
  ],
};

/**
 * Benchmark Test Thresholds
 * Strict thresholds for isolated operation testing
 */
export const benchmarkThresholds = {
  'http_req_duration': [
    'p(95) < 75',      // Tighter bounds for benchmark
    'p(99) < 150',
    'avg < 40',
  ],

  'http_req_failed': [
    'rate < 0.0001',   // Very low error rate for benchmarks
  ],

  'mcp_tool_call_duration_ms': [
    'p(95) < 40',      // Tool call should be fast in isolation
  ],
};

/**
 * Quick Test Thresholds
 * For fast CI checks (relaxed)
 */
export const quickThresholds = {
  'http_req_duration': [
    'p(95) < 200',     // More relaxed for quick check
  ],

  'http_req_failed': [
    'rate < 0.01',     // 1% error rate acceptable
  ],
};

/**
 * Performance Targets Summary
 * Document the expected performance characteristics
 */
export const PerformanceTargets = {
  latency: {
    average: { target: 50, stretch: 30, unit: 'ms' },
    p95: { target: 100, stretch: 75, unit: 'ms' },
    p99: { target: 200, stretch: 150, unit: 'ms' },
  },
  throughput: {
    requests_per_second: { target: 1000, stretch: 2000, unit: 'req/s' },
    concurrent_sessions: { target: 100, stretch: 500, unit: 'sessions' },
  },
  reliability: {
    error_rate: { target: 0.1, stretch: 0.05, unit: '%' },
    uptime: { target: 99.9, stretch: 99.99, unit: '%' },
  },
  capacity: {
    max_vus_stress: { target: 300, stretch: 500, unit: 'VUs' },
  },
  resources: {
    cpu_usage: { target: 70, alert: 85, unit: '%' },
    memory_usage: { target: 512, alert: 1024, unit: 'MB' },
    memory_growth_rate: { target: 1, alert: 10, unit: 'MB/hour' },
  },
};

/**
 * Get thresholds by test type
 */
export function getThresholds(testType) {
  switch (testType) {
    case 'load':
      return loadThresholds;
    case 'stress':
      return stressThresholds;
    case 'endurance':
      return enduranceThresholds;
    case 'spike':
      return spikeThresholds;
    case 'benchmark':
      return benchmarkThresholds;
    case 'quick':
      return quickThresholds;
    default:
      return loadThresholds;
  }
}

/**
 * Custom threshold checks for specific metrics
 */
export function checkCustomThresholds(metrics) {
  const issues = [];

  // Check protocol overhead (should be 1-5ms)
  if (metrics.protocol_overhead_ms) {
    const avg = metrics.protocol_overhead_ms.avg;
    if (avg < 1) {
      issues.push({
        metric: 'protocol_overhead_ms',
        severity: 'warning',
        message: `Protocol overhead suspiciously low: ${avg}ms (expected 1-5ms)`,
      });
    } else if (avg > 10) {
      issues.push({
        metric: 'protocol_overhead_ms',
        severity: 'error',
        message: `Protocol overhead too high: ${avg}ms (expected 1-5ms)`,
      });
    }
  }

  // Check session reuse rate (should be high)
  if (metrics.mcp_session_reuse_rate) {
    const rate = metrics.mcp_session_reuse_rate.rate;
    if (rate < 0.5) {
      issues.push({
        metric: 'mcp_session_reuse_rate',
        severity: 'warning',
        message: `Low session reuse rate: ${rate * 100}% (expected > 50%)`,
      });
    }
  }

  // Check for memory leaks (increasing trend in memory)
  if (metrics.memory_trend) {
    const slope = metrics.memory_trend.slope;
    if (slope > 10) {
      issues.push({
        metric: 'memory_trend',
        severity: 'error',
        message: `Possible memory leak detected: ${slope}MB/hour growth rate`,
      });
    }
  }

  return issues;
}
