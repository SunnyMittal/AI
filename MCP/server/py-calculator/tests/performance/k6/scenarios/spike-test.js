/**
 * Spike Test for MCP Calculator Server
 *
 * Purpose: Test recovery from sudden traffic bursts
 * Duration: ~12 minutes
 * Profile:
 *   - Baseline: 10 VUs
 *   - Spike: Instant jump to 200 VUs (hold 1 min)
 *   - Drop: Back to 10 VUs
 *   - Repeat: 5 cycles
 *
 * Monitored Metrics:
 *   - Response time during spike
 *   - Error rate during spike
 *   - Recovery time after spike
 *   - System stability after recovery
 */

import { sleep } from 'k6';
import { initializeSession, callTool, deleteSession } from '../lib/mcp-client.js';
import { getRealisticOperation } from '../lib/test-data.js';
import { spikeTestThresholds } from '../lib/thresholds.js';

export const options = {
    stages: [
        // Initial baseline
        { duration: '30s', target: 10 },   // Baseline

        // Spike 1
        { duration: '10s', target: 200 },  // Spike
        { duration: '1m', target: 200 },   // Hold spike
        { duration: '10s', target: 10 },   // Recovery
        { duration: '1m', target: 10 },    // Baseline

        // Spike 2
        { duration: '10s', target: 200 },
        { duration: '1m', target: 200 },
        { duration: '10s', target: 10 },
        { duration: '1m', target: 10 },

        // Spike 3
        { duration: '10s', target: 200 },
        { duration: '1m', target: 200 },
        { duration: '10s', target: 10 },
        { duration: '1m', target: 10 },

        // Spike 4
        { duration: '10s', target: 200 },
        { duration: '1m', target: 200 },
        { duration: '10s', target: 10 },
        { duration: '1m', target: 10 },

        // Spike 5
        { duration: '10s', target: 200 },
        { duration: '1m', target: 200 },
        { duration: '10s', target: 10 },
        { duration: '30s', target: 10 },   // Final baseline

        { duration: '10s', target: 0 },    // Ramp down
    ],
    thresholds: spikeTestThresholds,
};

export function setup() {
    console.log('========================================');
    console.log('Starting Spike Test');
    console.log('Duration: ~12 minutes');
    console.log('Pattern: 10 VUs ↔ 200 VUs (5 cycles)');
    console.log('Purpose: Test recovery from traffic bursts');
    console.log('========================================');
}

export default function () {
    // Initialize session
    const sessionId = initializeSession();

    if (!sessionId) {
        console.error('Failed to initialize session');
        sleep(0.5);
        return;
    }

    // Perform 3 operations per iteration
    for (let i = 0; i < 3; i++) {
        const { operation, args } = getRealisticOperation();

        const result = callTool(sessionId, operation, args);

        if (result.error) {
            console.error(`Operation ${operation} failed: ${result.error}`);
        }

        // Minimal delay
        sleep(0.1);
    }

    // Cleanup
    deleteSession(sessionId);

    // Variable think time based on load
    sleep(0.5 + Math.random() * 0.5);
}

export function teardown(data) {
    console.log('========================================');
    console.log('Spike Test Complete');
    console.log('Review recovery patterns and error rates');
    console.log('========================================');
}
