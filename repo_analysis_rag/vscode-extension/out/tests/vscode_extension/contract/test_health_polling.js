"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const assert = __importStar(require("assert"));
const agentClient_1 = require("../../../vscode-extension/src/services/agentClient");
describe("Health Polling Contract Test", () => {
    let originalFetch;
    before(() => {
        originalFetch = global.fetch;
    });
    after(() => {
        global.fetch = originalFetch;
    });
    it("polls at ~2 second intervals and stops when indexing=false", async function () {
        this.timeout(10000);
        let callCount = 0;
        const callTimes = [];
        global.fetch = (async (url) => {
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
            };
        });
        const updates = [];
        (0, agentClient_1.startHealthPolling)("http://localhost:8000", (health) => {
            updates.push(health);
        }, (err) => {
            assert.fail(`Polling should not error: ${err.message}`);
        });
        // Wait for 3 calls (initial + 2 intervals of 2s = ~4s)
        await new Promise(resolve => setTimeout(resolve, 5000));
        (0, agentClient_1.stopHealthPolling)();
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
    it("stops polling on error", async function () {
        this.timeout(5000);
        let callCount = 0;
        global.fetch = (async () => {
            callCount++;
            throw new Error("Network error");
        });
        let errorReceived = false;
        (0, agentClient_1.startHealthPolling)("http://localhost:8000", () => { }, () => {
            errorReceived = true;
        });
        await new Promise(resolve => setTimeout(resolve, 500));
        assert.strictEqual(callCount, 1, "Should have called once and then stopped");
        assert.ok(errorReceived, "Error callback should have been triggered");
        (0, agentClient_1.stopHealthPolling)();
    });
});
