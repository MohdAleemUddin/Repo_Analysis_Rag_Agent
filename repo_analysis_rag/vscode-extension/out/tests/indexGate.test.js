"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const node_assert_1 = __importDefault(require("node:assert"));
const node_fs_1 = __importDefault(require("node:fs"));
const node_os_1 = __importDefault(require("node:os"));
const node_path_1 = __importDefault(require("node:path"));
const pathNormalize_1 = require("../vscode-extension/src/utils/pathNormalize");
const indexGate_1 = require("../vscode-extension/src/services/indexGate");
const indexingState_1 = require("../vscode-extension/src/services/indexingState");
async function runTests() {
    const tempBase = await node_fs_1.default.promises.mkdtemp(node_path_1.default.join(node_os_1.default.tmpdir(), "index-gate-test-"));
    const storageRoot = node_path_1.default.join(tempBase, "storage");
    const repoRoot = node_path_1.default.join(tempBase, "repo");
    await node_fs_1.default.promises.mkdir(storageRoot, { recursive: true });
    await node_fs_1.default.promises.mkdir(repoRoot, { recursive: true });
    const config = { storageRoot };
    const normalized = (0, pathNormalize_1.normalizeRootPath)(repoRoot);
    node_assert_1.default.ok(normalized.length > 0, "Normalized path should be populated");
    const initialExists = await (0, indexGate_1.checkIndexExists)(config, repoRoot);
    node_assert_1.default.strictEqual(initialExists, false, "Index should not exist yet");
    const indexDir = (0, indexGate_1.getIndexDir)(config, repoRoot);
    await node_fs_1.default.promises.mkdir(indexDir, { recursive: true });
    const afterCreation = await (0, indexGate_1.checkIndexExists)(config, repoRoot);
    node_assert_1.default.strictEqual(afterCreation, true, "Index directory should be detected");
    (0, indexingState_1.setIndexing)(normalized);
    node_assert_1.default.strictEqual((0, indexingState_1.isIndexing)(normalized), true, "Indexing state should be true once set");
    (0, indexingState_1.clearIndexing)(normalized);
    node_assert_1.default.strictEqual((0, indexingState_1.isIndexing)(normalized), false, "Indexing state should be false after clearing");
    await node_fs_1.default.promises.rm(tempBase, { recursive: true, force: true });
    console.log("All index gate tests passed.");
}
runTests().catch((error) => {
    console.error(error);
    process.exit(1);
});
