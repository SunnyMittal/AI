import { check } from 'k6';
import { Trend, Counter } from 'k6/metrics';
import { initializeSession, callTool, deleteSession } from '../lib/mcp-client.js';
import { generateNumberPair, generateEdgeCases, validateResult, getExpectedResult } from '../lib/test-data.js';
import { benchmarkThresholds } from '../lib/thresholds.js';

// Per-operation metrics
const addDuration = new Trend('operation_add_ms');
const subtractDuration = new Trend('operation_subtract_ms');
const multiplyDuration = new Trend('operation_multiply_ms');
const divideDuration = new Trend('operation_divide_ms');

// Operation counters
const addCount = new Counter('operation_add_count');
const subtractCount = new Counter('operation_subtract_count');
const multiplyCount = new Counter('operation_multiply_count');
const divideCount = new Counter('operation_divide_count');

// Edge case tracking
const edgeCasesPassed = new Counter('edge_cases_passed');
const edgeCasesFailed = new Counter('edge_cases_failed');

// Test options
export const options = {
  scenarios: {
    // Test add operation
    benchmark_add: {
      executor: 'constant-vus',
      exec: 'testAddOperation',
      vus: 10,
      duration: '1m',
    },
    // Test subtract operation
    benchmark_subtract: {
      executor: 'constant-vus',
      exec: 'testSubtractOperation',
      vus: 10,
      duration: '1m',
      startTime: '1m',
    },
    // Test multiply operation
    benchmark_multiply: {
      executor: 'constant-vus',
      exec: 'testMultiplyOperation',
      vus: 10,
      duration: '1m',
      startTime: '2m',
    },
    // Test divide operation
    benchmark_divide: {
      executor: 'constant-vus',
      exec: 'testDivideOperation',
      vus: 10,
      duration: '1m',
      startTime: '3m',
    },
    // Test edge cases
    edge_cases: {
      executor: 'shared-iterations',
      exec: 'testEdgeCases',
      vus: 1,
      iterations: 1,
      startTime: '4m',
    },
  },
  thresholds: benchmarkThresholds,
};

let sessionId = null;

// Initialize session for each scenario
function ensureSession() {
  if (!sessionId) {
    sessionId = initializeSession();
    if (!sessionId) {
      throw new Error('Failed to initialize session');
    }
  }
  return sessionId;
}

// Test add operation
export function testAddOperation() {
  const sid = ensureSession();
  const { a, b } = generateNumberPair('mixed');

  const start = Date.now();
  const result = callTool(sid, 'add', { a, b });
  const duration = Date.now() - start;

  addDuration.add(duration);
  addCount.add(1);

  check(result, {
    'add: result is success': (r) => r && r.success,
    'add: result is valid': (r) => {
      if (!r || !r.success) return false;
      const expected = getExpectedResult('add', a, b);
      return validateResult(r.value, expected);
    },
  });
}

// Test subtract operation
export function testSubtractOperation() {
  const sid = ensureSession();
  const { a, b } = generateNumberPair('mixed');

  const start = Date.now();
  const result = callTool(sid, 'subtract', { a, b });
  const duration = Date.now() - start;

  subtractDuration.add(duration);
  subtractCount.add(1);

  check(result, {
    'subtract: result is success': (r) => r && r.success,
    'subtract: result is valid': (r) => {
      if (!r || !r.success) return false;
      const expected = getExpectedResult('subtract', a, b);
      return validateResult(r.value, expected);
    },
  });
}

// Test multiply operation
export function testMultiplyOperation() {
  const sid = ensureSession();
  const { a, b } = generateNumberPair('mixed');

  const start = Date.now();
  const result = callTool(sid, 'multiply', { a, b });
  const duration = Date.now() - start;

  multiplyDuration.add(duration);
  multiplyCount.add(1);

  check(result, {
    'multiply: result is success': (r) => r && r.success,
    'multiply: result is valid': (r) => {
      if (!r || !r.success) return false;
      const expected = getExpectedResult('multiply', a, b);
      return validateResult(r.value, expected);
    },
  });
}

// Test divide operation
export function testDivideOperation() {
  const sid = ensureSession();
  const { a, b } = generateNumberPair('decimal');

  // Ensure b is not zero for normal division tests
  const bNonZero = b === 0 ? 1.5 : b;

  const start = Date.now();
  const result = callTool(sid, 'divide', { a, b: bNonZero });
  const duration = Date.now() - start;

  divideDuration.add(duration);
  divideCount.add(1);

  check(result, {
    'divide: result is success': (r) => r && r.success,
    'divide: result is valid': (r) => {
      if (!r || !r.success) return false;
      const expected = getExpectedResult('divide', a, bNonZero);
      return validateResult(r.value, expected, 0.001); // Larger epsilon for division
    },
  });
}

// Test edge cases
export function testEdgeCases() {
  const sid = ensureSession();
  const edgeCases = generateEdgeCases();

  console.log(`Testing ${edgeCases.length} edge cases...`);

  for (const testCase of edgeCases) {
    const { operation, a, b, description } = testCase;

    const result = callTool(sid, operation, { a, b });
    const expected = getExpectedResult(operation, a, b);

    let passed = false;

    // Special handling for division by zero
    if (operation === 'divide' && b === 0) {
      // Division by zero should return error
      passed = result && !result.success;
      if (passed) {
        console.log(`✓ Edge case passed: ${description} - correctly returned error`);
      } else {
        console.log(`✗ Edge case failed: ${description} - should return error for division by zero`);
      }
    } else {
      // Normal validation
      if (result && result.success) {
        passed = validateResult(result.value, expected, 0.001);
        if (passed) {
          console.log(`✓ Edge case passed: ${description} = ${result.value}`);
        } else {
          console.log(`✗ Edge case failed: ${description} - got ${result.value}, expected ${expected}`);
        }
      } else {
        console.log(`✗ Edge case failed: ${description} - tool call failed`);
      }
    }

    if (passed) {
      edgeCasesPassed.add(1);
    } else {
      edgeCasesFailed.add(1);
    }
  }

  console.log(`Edge cases: ${edgeCasesPassed} passed, ${edgeCasesFailed} failed`);
}

// Teardown for all scenarios
export function teardown() {
  if (sessionId) {
    deleteSession(sessionId);
    sessionId = null;
  }
  console.log('Benchmark tests completed');
}
