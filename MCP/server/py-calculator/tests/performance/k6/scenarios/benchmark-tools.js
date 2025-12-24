/**
 * Benchmark Test for MCP Calculator Server
 *
 * Purpose: Measure individual operation performance
 * Duration: ~5 minutes
 * Test Focus:
 *   - Isolated testing per operation (add, subtract, multiply, divide)
 *   - Various number ranges (small, large, decimals, negatives)
 *   - Protocol overhead calculation
 *   - Consistent performance measurement
 */

import { sleep } from 'k6';
import { initializeSession, callTool, deleteSession } from '../lib/mcp-client.js';
import { randomArgs, getTestCase } from '../lib/test-data.js';
import { benchmarkThresholds } from '../lib/thresholds.js';

export const options = {
    scenarios: {
        // Benchmark add operation
        benchmark_add: {
            executor: 'constant-vus',
            vus: 10,
            duration: '1m',
            exec: 'benchmarkAdd',
        },
        // Benchmark subtract operation
        benchmark_subtract: {
            executor: 'constant-vus',
            vus: 10,
            duration: '1m',
            exec: 'benchmarkSubtract',
            startTime: '1m',
        },
        // Benchmark multiply operation
        benchmark_multiply: {
            executor: 'constant-vus',
            vus: 10,
            duration: '1m',
            exec: 'benchmarkMultiply',
            startTime: '2m',
        },
        // Benchmark divide operation
        benchmark_divide: {
            executor: 'constant-vus',
            vus: 10,
            duration: '1m',
            exec: 'benchmarkDivide',
            startTime: '3m',
        },
        // Mixed operations
        benchmark_mixed: {
            executor: 'constant-vus',
            vus: 20,
            duration: '1m',
            exec: 'benchmarkMixed',
            startTime: '4m',
        },
    },
    thresholds: benchmarkThresholds,
};

export function setup() {
    console.log('========================================');
    console.log('Starting Benchmark Test');
    console.log('Duration: ~5 minutes');
    console.log('Testing individual operations');
    console.log('========================================');
}

/**
 * Benchmark addition operation
 */
export function benchmarkAdd() {
    const sessionId = initializeSession();
    if (!sessionId) return;

    // Test with different number types
    const testCases = [
        getTestCase('small'),
        getTestCase('large'),
        getTestCase('decimal'),
        getTestCase('negative'),
        getTestCase('mixed'),
    ];

    for (const args of testCases) {
        callTool(sessionId, 'add', args);
        sleep(0.1);
    }

    deleteSession(sessionId);
    sleep(0.5);
}

/**
 * Benchmark subtraction operation
 */
export function benchmarkSubtract() {
    const sessionId = initializeSession();
    if (!sessionId) return;

    const testCases = [
        getTestCase('small'),
        getTestCase('large'),
        getTestCase('decimal'),
        getTestCase('negative'),
        getTestCase('mixed'),
    ];

    for (const args of testCases) {
        callTool(sessionId, 'subtract', args);
        sleep(0.1);
    }

    deleteSession(sessionId);
    sleep(0.5);
}

/**
 * Benchmark multiplication operation
 */
export function benchmarkMultiply() {
    const sessionId = initializeSession();
    if (!sessionId) return;

    const testCases = [
        getTestCase('small'),
        getTestCase('large'),
        getTestCase('decimal'),
        getTestCase('negative'),
        getTestCase('mixed'),
    ];

    for (const args of testCases) {
        callTool(sessionId, 'multiply', args);
        sleep(0.1);
    }

    deleteSession(sessionId);
    sleep(0.5);
}

/**
 * Benchmark division operation
 */
export function benchmarkDivide() {
    const sessionId = initializeSession();
    if (!sessionId) return;

    const testCases = [
        getTestCase('small'),
        getTestCase('large'),
        getTestCase('decimal'),
        getTestCase('negative'),
        getTestCase('mixed'),
    ];

    for (const args of testCases) {
        // Ensure b is not zero for division
        if (args.b === 0) {
            args.b = 1;
        }
        callTool(sessionId, 'divide', args);
        sleep(0.1);
    }

    deleteSession(sessionId);
    sleep(0.5);
}

/**
 * Benchmark mixed operations
 */
export function benchmarkMixed() {
    const sessionId = initializeSession();
    if (!sessionId) return;

    const operations = ['add', 'subtract', 'multiply', 'divide'];

    for (const operation of operations) {
        const args = randomArgs(operation);
        callTool(sessionId, operation, args);
        sleep(0.05);
    }

    deleteSession(sessionId);
    sleep(0.3);
}

export function teardown(data) {
    console.log('========================================');
    console.log('Benchmark Test Complete');
    console.log('Review per-operation metrics:');
    console.log('  - operation_add_ms');
    console.log('  - operation_subtract_ms');
    console.log('  - operation_multiply_ms');
    console.log('  - operation_divide_ms');
    console.log('========================================');
}
