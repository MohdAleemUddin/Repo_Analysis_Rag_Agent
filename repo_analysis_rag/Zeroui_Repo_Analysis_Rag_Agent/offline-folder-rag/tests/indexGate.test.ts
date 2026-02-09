import assert from "node:assert";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import { normalizeRootPath } from "../vscode-extension/src/utils/pathNormalize";
import { getIndexDir, checkIndexExists } from "../vscode-extension/src/services/indexGate";
import { setIndexing, isIndexing, clearIndexing } from "../vscode-extension/src/services/indexingState";

async function runTests(): Promise<void> {
    const tempBase = await fs.promises.mkdtemp(path.join(os.tmpdir(), "index-gate-test-"));
    const storageRoot = path.join(tempBase, "storage");
    const repoRoot = path.join(tempBase, "repo");

    await fs.promises.mkdir(storageRoot, { recursive: true });
    await fs.promises.mkdir(repoRoot, { recursive: true });

    const config = { storageRoot };
    const normalized = normalizeRootPath(repoRoot);
    assert.ok(normalized.length > 0, "Normalized path should be populated");

    const initialExists = await checkIndexExists(config, repoRoot);
    assert.strictEqual(initialExists, false, "Index should not exist yet");

    const indexDir = getIndexDir(config, repoRoot);
    await fs.promises.mkdir(indexDir, { recursive: true });

    const afterCreation = await checkIndexExists(config, repoRoot);
    assert.strictEqual(afterCreation, true, "Index directory should be detected");

    setIndexing(normalized);
    assert.strictEqual(isIndexing(normalized), true, "Indexing state should be true once set");

    clearIndexing(normalized);
    assert.strictEqual(isIndexing(normalized), false, "Indexing state should be false after clearing");

    await fs.promises.rm(tempBase, { recursive: true, force: true });

    console.log("All index gate tests passed.");
}

runTests().catch((error) => {
    console.error(error);
    process.exit(1);
});
