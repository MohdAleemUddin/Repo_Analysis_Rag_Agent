"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AutoIndexScheduler = void 0;
const agentClient_1 = require("./agentClient");
const DEBOUNCE_MS = 60_000;
const RATE_LIMIT_MS = 5 * 60_000;
const HEALTH_POLL_MS = 2_000;
class AutoIndexScheduler {
    lastStartTime = 0;
    debounceTimer;
    isWaitingForHealth = false;
    triggerIndex;
    getRootPath;
    agentBaseUrl;
    constructor(options) {
        this.triggerIndex = options.triggerIndex;
        this.getRootPath = options.getRootPath;
        this.agentBaseUrl = options.agentBaseUrl;
    }
    requestIndex() {
        if (this.isRateLimited()) {
            return;
        }
        this.clearDebounceTimer();
        this.debounceTimer = setTimeout(() => void this.startIndex(), DEBOUNCE_MS);
    }
    stop() {
        this.clearDebounceTimer();
    }
    isRateLimited() {
        return Date.now() - this.lastStartTime < RATE_LIMIT_MS;
    }
    clearDebounceTimer() {
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
            this.debounceTimer = undefined;
        }
    }
    async startIndex() {
        if (this.isRateLimited() || this.isWaitingForHealth) {
            return;
        }
        const rootPath = this.getRootPath();
        if (!rootPath) {
            return;
        }
        this.isWaitingForHealth = true;
        try {
            // Wait for health to be clear (indexing: false) before starting
            if (!(await this.awaitHealthClear())) {
                return;
            }
            await this.triggerIndex();
            this.lastStartTime = Date.now();
        }
        finally {
            this.isWaitingForHealth = false;
        }
    }
    async awaitHealthClear() {
        while (true) {
            const health = await this.fetchHealth();
            if (!health) {
                // If we can't fetch health, assume it's busy or agent is down, 
                // but for the sake of retrying as per Task 3, we wait.
                await this.delay(2000);
                continue;
            }
            if (!health.indexing) {
                return true;
            }
            await this.delay(2000); // 2 seconds delay as per Task 3
        }
    }
    async fetchHealth() {
        return (0, agentClient_1.fetchHealth)(this.agentBaseUrl);
    }
    async delay(ms) {
        return new Promise((resolve) => setTimeout(resolve, ms));
    }
}
exports.AutoIndexScheduler = AutoIndexScheduler;
