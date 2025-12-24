/**
 * Load Test for MCP Calculator Server
 *
 * Purpose: Establish baseline performance under realistic load
 * Duration: ~14 minutes
 * Profile:
 *   - Ramp up: 0 → 50 VUs (1 min)
 *   - Sustain: 50 VUs (5 min)
 *   - Ramp up: 50 → 100 VUs (1 min)
 *   - Sustain: 100 VUs (5 min)
 *   - Ramp down: 100 → 0 (1 min)
 *
 * Operations Mix:
 *   - 40% add operations
 *   - 30% subtract operations
 *   - 20% multiply operations
 *   - 10% divide operations
 */

import { sleep } from 'k6';
import { initializeSession, callTool, deleteSession } from '../lib/mcp-client.js';
import { getRealisticOperation } from '../lib/test-data.js';
import { loadTestThresholds, quickTestThresholds } from '../lib/thresholds.js';

// Use quick test thresholds if running with short duration (< 5 minutes)
const isQuickTest = __ENV.TEST_DURATION && __ENV.TEST_DURATION.includes('s');
const thresholds = isQuickTest ? quickTestThresholds : loadTestThresholds;

export const options = {
    stages: [
        { duration: '1m', target: 50 },   // Ramp up to 50 VUs
        { duration: '5m', target: 50 },   // Stay at 50 VUs
        { duration: '1m', target: 100 },  // Ramp up to 100 VUs
        { duration: '5m', target: 100 },  // Stay at 100 VUs
        { duration: '1m', target: 0 },    // Ramp down to 0 VUs
    ],
    thresholds: thresholds,
};

export function setup() {
    console.log('========================================');
    console.log('Starting Load Test');
    console.log('Duration: ~14 minutes');
    console.log('Max VUs: 100');
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

    // Small delay after session creation
    sleep(0.5);

    // Perform 3 random operations per iteration (reduced from 5)
    for (let i = 0; i < 3; i++) {
        const { operation, args } = getRealisticOperation();

        const result = callTool(sessionId, operation, args);

        if (result.error) {
            console.error(`Operation ${operation} failed: ${result.error}`);
        }

        // Delay between operations (200-500ms)
        sleep(0.2 + Math.random() * 0.3);
    }

    // Cleanup
    deleteSession(sessionId);

    // Think time between iterations (1-3 seconds)
    sleep(1 + Math.random() * 2);
}

export function teardown(data) {
    console.log('========================================');
    console.log('Load Test Complete');
    console.log('========================================');
}
