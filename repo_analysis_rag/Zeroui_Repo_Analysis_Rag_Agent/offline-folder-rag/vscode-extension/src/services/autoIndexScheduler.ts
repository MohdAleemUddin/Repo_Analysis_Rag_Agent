import { authenticatedFetch, fetchHealth } from "./agentClient";

const DEBOUNCE_MS = 60_000;
const RATE_LIMIT_MS = 5 * 60_000;
const HEALTH_POLL_MS = 2_000;

type AutoIndexSchedulerOptions = {
    triggerIndex: () => Promise<void>;
    getRootPath: () => string | undefined;
    agentBaseUrl: string;
};

export class AutoIndexScheduler {
    private lastStartTime = 0;
    private debounceTimer: NodeJS.Timeout | undefined;
    private isWaitingForHealth = false;
    private readonly triggerIndex: () => Promise<void>;
    private readonly getRootPath: () => string | undefined;
    private readonly agentBaseUrl: string;

    constructor(options: AutoIndexSchedulerOptions) {
        this.triggerIndex = options.triggerIndex;
        this.getRootPath = options.getRootPath;
        this.agentBaseUrl = options.agentBaseUrl;
    }

    public requestIndex(): void {
        if (this.isRateLimited()) {
            return;
        }

        this.clearDebounceTimer();
        this.debounceTimer = setTimeout(() => void this.startIndex(), DEBOUNCE_MS);
    }

    public stop(): void {
        this.clearDebounceTimer();
    }

    private isRateLimited(): boolean {
        return Date.now() - this.lastStartTime < RATE_LIMIT_MS;
    }

    private clearDebounceTimer(): void {
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
            this.debounceTimer = undefined;
        }
    }

    private async startIndex(): Promise<void> {
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
        } finally {
            this.isWaitingForHealth = false;
        }
    }

    private async awaitHealthClear(): Promise<boolean> {
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

    private async fetchHealth(): Promise<{ indexing: boolean } | null> {
        return fetchHealth(this.agentBaseUrl);
    }

    private async delay(ms: number): Promise<void> {
        return new Promise((resolve) => setTimeout(resolve, ms));
    }
}
