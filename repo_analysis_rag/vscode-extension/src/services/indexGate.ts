import crypto from "crypto";
import fs from "fs";
import path from "path";

import { normalizeRootPath } from "../utils/pathNormalize";

export interface IndexGateConfig {
    storageRoot: string;
}

const MANIFEST_FILE = "manifest.json";

export function isPathInsideRoot(rootPath: string, targetPath: string): boolean {
    const normalizedRoot = normalizeRootPath(rootPath);
    const normalizedTarget = path.resolve(targetPath);
    return normalizedTarget.startsWith(normalizedRoot);
}

function getRepoId(normalizedRootPath: string): string {
    return crypto.createHash("sha256").update(normalizedRootPath).digest("hex");
}

export function getIndexDir(config: IndexGateConfig, rootPath: string): string {
    const normalizedRootPath = normalizeRootPath(rootPath);
    const repoId = getRepoId(normalizedRootPath);
    return path.join(config.storageRoot, "indexes", repoId);
}

function getManifestPath(dir: string): string {
    return path.join(dir, MANIFEST_FILE);
}

export async function checkIndexExists(config: IndexGateConfig, rootPath: string): Promise<boolean> {
    const normalizedRootPath = normalizeRootPath(rootPath);
    const dir = getIndexDir(config, rootPath);
    const manifestPath = getManifestPath(dir);

    try {
        const content = await fs.promises.readFile(manifestPath, "utf-8");
        const parsed = JSON.parse(content);
        return (
            parsed?.repoId === getRepoId(normalizedRootPath) &&
            parsed?.rootPath === normalizedRootPath
        );
    } catch {
        return false;
    }
}

export async function triggerFullIndex(
    config: IndexGateConfig,
    rootPath: string,
    onProgress?: (message: string) => void
): Promise<void> {
    const normalizedRootPath = normalizeRootPath(rootPath);
    const dir = getIndexDir(config, rootPath);
    await fs.promises.mkdir(path.dirname(dir), { recursive: true });
    await fs.promises.mkdir(dir, { recursive: true });
    onProgress?.("Index directory prepared.");

    const manifestPath = getManifestPath(dir);
    const metadata = {
        repoId: getRepoId(normalizedRootPath),
        rootPath: normalizedRootPath,
        indexedAt: new Date().toISOString(),
    };

    await fs.promises.writeFile(manifestPath, JSON.stringify(metadata, null, 2), "utf-8");
    onProgress?.("Indexing complete.");
}

export { setIndexing, isIndexing, clearIndexing } from "./indexingState";
