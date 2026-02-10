"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.clearIndexing = exports.isIndexing = exports.setIndexing = void 0;
exports.isPathInsideRoot = isPathInsideRoot;
exports.getIndexDir = getIndexDir;
exports.checkIndexExists = checkIndexExists;
exports.triggerFullIndex = triggerFullIndex;
const crypto_1 = __importDefault(require("crypto"));
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const pathNormalize_1 = require("../utils/pathNormalize");
const MANIFEST_FILE = "manifest.json";
function isPathInsideRoot(rootPath, targetPath) {
    const normalizedRoot = (0, pathNormalize_1.normalizeRootPath)(rootPath);
    const normalizedTarget = path_1.default.resolve(targetPath);
    return normalizedTarget.startsWith(normalizedRoot);
}
function getRepoId(normalizedRootPath) {
    return crypto_1.default.createHash("sha256").update(normalizedRootPath).digest("hex");
}
function getIndexDir(config, rootPath) {
    const normalizedRootPath = (0, pathNormalize_1.normalizeRootPath)(rootPath);
    const repoId = getRepoId(normalizedRootPath);
    return path_1.default.join(config.storageRoot, "indexes", repoId);
}
function getManifestPath(dir) {
    return path_1.default.join(dir, MANIFEST_FILE);
}
async function checkIndexExists(config, rootPath) {
    const normalizedRootPath = (0, pathNormalize_1.normalizeRootPath)(rootPath);
    const dir = getIndexDir(config, rootPath);
    const manifestPath = getManifestPath(dir);
    try {
        const content = await fs_1.default.promises.readFile(manifestPath, "utf-8");
        const parsed = JSON.parse(content);
        return (parsed?.repoId === getRepoId(normalizedRootPath) &&
            parsed?.rootPath === normalizedRootPath);
    }
    catch {
        return false;
    }
}
async function triggerFullIndex(config, rootPath, onProgress) {
    const normalizedRootPath = (0, pathNormalize_1.normalizeRootPath)(rootPath);
    const dir = getIndexDir(config, rootPath);
    await fs_1.default.promises.mkdir(path_1.default.dirname(dir), { recursive: true });
    await fs_1.default.promises.mkdir(dir, { recursive: true });
    onProgress?.("Index directory prepared.");
    const manifestPath = getManifestPath(dir);
    const metadata = {
        repoId: getRepoId(normalizedRootPath),
        rootPath: normalizedRootPath,
        indexedAt: new Date().toISOString(),
    };
    await fs_1.default.promises.writeFile(manifestPath, JSON.stringify(metadata, null, 2), "utf-8");
    onProgress?.("Indexing complete.");
}
var indexingState_1 = require("./indexingState");
Object.defineProperty(exports, "setIndexing", { enumerable: true, get: function () { return indexingState_1.setIndexing; } });
Object.defineProperty(exports, "isIndexing", { enumerable: true, get: function () { return indexingState_1.isIndexing; } });
Object.defineProperty(exports, "clearIndexing", { enumerable: true, get: function () { return indexingState_1.clearIndexing; } });
