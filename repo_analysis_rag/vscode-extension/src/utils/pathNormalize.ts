import * as path from 'path';
import * as crypto from 'crypto';

/**
 * Normalizes a root path to a standard format matching the Python implementation.
 * @param rawPath The path to normalize.
 * @returns The normalized path string.
 */
export function normalizeRootPath(rawPath: string): string {
    if (rawPath === null || rawPath === undefined || rawPath === "") {
        throw new Error("Invalid root path: path cannot be empty");
    }

    // Convert to absolute path
    let absPath = path.resolve(rawPath);

    // Normalize path (handles . and ..)
    let normPath = path.normalize(absPath);

    // Replace all forward slashes with backslashes
    normPath = normPath.replace(/\//g, '\\');

    // Remove trailing backslash except for Windows drive root (e.g., "C:\")
    if (normPath.endsWith('\\') && !(normPath.length === 3 && normPath.charAt(1) === ':' && normPath.charAt(2) === '\\')) {
        normPath = normPath.slice(0, -1);
    }

    // Convert entire string to lowercase
    return normPath.toLowerCase();
}

/**
 * Computes a unique repo ID from a normalized path matching the Python implementation.
 * @param normalizedPath The normalized path string.
 * @returns The SHA256 hash as a lowercase hex string.
 */
export function computeRepoId(normalizedPath: string): string {
    return crypto.createHash('sha256').update(normalizedPath, 'utf-8').digest('hex').toLowerCase();
}

export { normalizeRootPath as normalizeRootPathFunc, computeRepoId as computeRepoIdFunc };
