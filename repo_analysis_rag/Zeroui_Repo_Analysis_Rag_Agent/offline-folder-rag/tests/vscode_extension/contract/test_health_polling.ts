import * as assert from "assert";
import * as path from "path";

import { startHealthPolling, stopHealthPolling } from "../../../vscode-extension/src/services/agentClient";

describe("Health Polling Contract Test", () => {
    let originalFetch: typeof fetch;

    before(() => {
        originalFetch = global.fetch;
    });

    after(() => {
        global.fetch = originalFetch;
    });

    it("polls at ~2 second intervals and stops when indexing=false", async function() {
        this.timeout(10000);

        let callCount = 0;
        const callTimes: number[] = [];

        global.fetch = (async (url: string) => {
            callCount++;
            callTimes.push(Date.now());
            
            // First two calls return indexing=true, third returns indexing=false
            const indexing = callCount < 3;
            
            return {
                ok: true,
                json: async () => ({
                    indexing,
                    indexed_files_so_far: callCount * 10,
                    estimated_total_files: 100,
                    last_index_completed_epoch_ms: 0,
                    ollama_ok: true,
                    ripgrep_ok: true,
                    chroma_ok: true
                })
            } as Response;
        }) as any;

        const updates: any[] = [];
        startHealthPolling(
            "http://localhost:8000",
            (health: any) => {
                updates.push(health);
            },
            (err: any) => {
                assert.fail(`Polling should not error: ${err.message}`);
            }
        );

        // Wait for 3 calls (initial + 2 intervals of 2s = ~4s)
        await new Promise(resolve => setTimeout(resolve, 5000));

        stopHealthPolling();

        assert.strictEqual(callCount, 3, "Should have polled 3 times");
        assert.strictEqual(updates.length, 3, "Should have received 3 updates");
        
        // Verify intervals
        if (callTimes.length >= 2) {
            const interval1 = callTimes[1] - callTimes[0];
            const interval2 = callTimes[2] - callTimes[1];
            assert.ok(interval1 >= 1800 && interval1 <= 2500, `Interval 1 (${interval1}ms) should be ~2000ms`);
            assert.ok(interval2 >= 1800 && interval2 <= 2500, `Interval 2 (${interval2}ms) should be ~2000ms`);
        }

        assert.strictEqual(updates[0].indexing, true);
        assert.strictEqual(updates[1].indexing, true);
        assert.strictEqual(updates[2].indexing, false);
    });

    it("stops polling on error", async function() {
        this.timeout(5000);

        let callCount = 0;
        global.fetch = (async () => {
            callCount++;
            throw new Error("Network error");
        }) as any;

        let errorReceived = false;
        startHealthPolling(
            "http://localhost:8000",
            () => {},
            () => {
                errorReceived = true;
            }
        );

        await new Promise(resolve => setTimeout(resolve, 500));
        assert.strictEqual(callCount, 1, "Should have called once and then stopped");
        assert.ok(errorReceived, "Error callback should have been triggered");
        
        stopHealthPolling();
    });
});
