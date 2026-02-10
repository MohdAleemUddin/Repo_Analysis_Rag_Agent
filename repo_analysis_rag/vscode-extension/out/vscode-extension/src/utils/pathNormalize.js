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
exports.normalizeRootPath = normalizeRootPath;
exports.normalizeRootPathFunc = normalizeRootPath;
exports.computeRepoId = computeRepoId;
exports.computeRepoIdFunc = computeRepoId;
const path = __importStar(require("path"));
const crypto = __importStar(require("crypto"));
/**
 * Normalizes a root path to a standard format matching the Python implementation.
 * @param rawPath The path to normalize.
 * @returns The normalized path string.
 */
function normalizeRootPath(rawPath) {
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
function computeRepoId(normalizedPath) {
    return crypto.createHash('sha256').update(normalizedPath, 'utf-8').digest('hex').toLowerCase();
}
