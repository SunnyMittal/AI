/**
 * Endurance Test for MCP Calculator Server
 *
 * Purpose: Long-running stability and memory leak detection
 * Duration: ~2 hours 10 minutes
 * Profile:
 *   - Ramp up: 0 → 50 VUs (5 min)
 *   - Sustain: 50 VUs (2 hours)
 *   - Ramp down: 50 → 0 (5 min)
 *
 * Monitored Metrics:
 *   - Memory growth over time
 *   - Session cleanup effectiveness
 *   - Response time degradation
 *   - Connection stability
 *   - Resource leaks
 */

import { sleep } from 'k6';
import { initializeSession, callTool, deleteSession } from '../lib/mcp-client.js';
import { getRealisticOperation } from '../lib/test-data.js';
import { enduranceTestThresholds } from '../lib/thresholds.js';

export const options = {
    stages: [
        { duration: '5m', target: 50 },    // Ramp up to 50 VUs
        { duration: '120m', target: 50 },  // Sustain 50 VUs for 2 hours
        { duration: '5m', target: 0 },     // Ramp down to 0 VUs
    ],
    thresholds: enduranceTestThresholds,
};

export function setup() {
    console.log('========================================');
    console.log('Starting Endurance Test');
    console.log('Duration: ~2 hours 10 minutes');
    console.log('Constant VUs: 50');
    console.log('Purpose: Detect memory leaks and degradation');
    console.log('========================================');

    return {
        startTime: new Date().toISOString(),
    };
}

export default function () {
    // Initialize session
    const sessionId = initializeSession();

    if (!sessionId) {
        console.error('Failed to initialize session');
        return;
    }

    // Perform 10 operations per iteration
    // This ensures continuous load over the long test duration
    for (let i = 0; i < 10; i++) {
        const { operation, args } = getRealisticOperation();

        const result = callTool(sessionId, operation, args);

        if (result.error) {
            console.error(`Operation ${operation} failed: ${result.error}`);
        }

        // Small delay between operations
        sleep(0.2);
    }

    // Cleanup
    deleteSession(sessionId);

    // Moderate think time to simulate realistic usage
    sleep(2 + Math.random() * 2);
}

export function teardown(data) {
    const endTime = new Date();
    const startTime = new Date(data.startTime);
    const duration = (endTime - startTime) / 1000 / 60; // minutes

    console.log('========================================');
    console.log('Endurance Test Complete');
    console.log(`Actual Duration: ${duration.toFixed(2)} minutes`);
    console.log('Check memory metrics for leaks');
    console.log('Review response time trends');
    console.log('========================================');
}
