/**
 * Stress Test for MCP Calculator Server
 *
 * Purpose: Find maximum capacity and breaking points
 * Duration: ~20 minutes
 * Profile:
 *   - Progressive ramp: 100 → 200 → 400 → 800 VUs
 *   - Hold each level for 3 minutes
 *   - Continue until failure or significant degradation
 *
 * Monitored Metrics:
 *   - Server response times under extreme load
 *   - Memory consumption
 *   - Error rates and failure modes
 *   - Graceful vs catastrophic failure
 */

import { sleep } from 'k6';
import { initializeSession, callTool, deleteSession } from '../lib/mcp-client.js';
import { getRealisticOperation } from '../lib/test-data.js';
import { stressTestThresholds } from '../lib/thresholds.js';

export const options = {
    stages: [
        { duration: '2m', target: 100 },   // Ramp to 100 VUs
        { duration: '3m', target: 100 },   // Hold at 100 VUs
        { duration: '2m', target: 200 },   // Ramp to 200 VUs
        { duration: '3m', target: 200 },   // Hold at 200 VUs
        { duration: '2m', target: 400 },   // Ramp to 400 VUs
        { duration: '3m', target: 400 },   // Hold at 400 VUs
        { duration: '2m', target: 800 },   // Ramp to 800 VUs (stress point)
        { duration: '3m', target: 800 },   // Hold at 800 VUs
        { duration: '2m', target: 0 },     // Ramp down
    ],
    thresholds: stressTestThresholds,
};

export function setup() {
    console.log('========================================');
    console.log('Starting Stress Test');
    console.log('Duration: ~20 minutes');
    console.log('Max VUs: 800 (progressive ramp)');
    console.log('WARNING: Expect degradation at high load');
    console.log('========================================');
}

export default function () {
    // Initialize session
    const sessionId = initializeSession();

    if (!sessionId) {
        console.error('Failed to initialize session');
        sleep(1); // Back off on failure
        return;
    }

    // Perform 3 operations per iteration (reduced from load test)
    for (let i = 0; i < 3; i++) {
        const { operation, args } = getRealisticOperation();

        const result = callTool(sessionId, operation, args);

        if (result.error) {
            console.error(`Operation ${operation} failed: ${result.error}`);
            // Continue testing even on errors to measure behavior under stress
        }

        // Minimal delay between operations
        sleep(0.1);
    }

    // Cleanup
    deleteSession(sessionId);

    // Minimal think time under stress
    sleep(0.5 + Math.random() * 0.5);
}

export function teardown(data) {
    console.log('========================================');
    console.log('Stress Test Complete');
    console.log('Review metrics to identify breaking points');
    console.log('========================================');
}
