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
const crypto = __importStar(require("crypto"));
const pathNormalize_1 = require("../../../vscode-extension/src/utils/pathNormalize");
describe('Path Normalization and Repo ID Contract Tests', () => {
    describe('normalizeRootPath', () => {
        it('should normalize basic paths with relative segments', () => {
            const path = "C:/test/../test";
            const normalized = (0, pathNormalize_1.normalizeRootPath)(path);
            assert.strictEqual(normalized.endsWith('test'), true);
            assert.strictEqual(normalized.includes('/'), false);
            assert.strictEqual(normalized, normalized.toLowerCase());
        });
        it('should replace forward slashes with backslashes and remove trailing slash', () => {
            const path = "C:/users/test/folder/";
            const normalized = (0, pathNormalize_1.normalizeRootPath)(path);
            assert.strictEqual(normalized.includes('\\'), true);
            assert.strictEqual(normalized.endsWith('\\'), false);
            assert.strictEqual(normalized, normalized.toLowerCase());
        });
        it('should preserve backslash for Windows drive root', () => {
            const path = "C:/";
            const normalized = (0, pathNormalize_1.normalizeRootPath)(path);
            assert.strictEqual(normalized, "c:\\");
        });
        it('should throw error for empty or null input', () => {
            assert.throws(() => (0, pathNormalize_1.normalizeRootPath)(""), /Invalid root path: path cannot be empty/);
            assert.throws(() => (0, pathNormalize_1.normalizeRootPath)(null), /Invalid root path: path cannot be empty/);
            assert.throws(() => (0, pathNormalize_1.normalizeRootPath)(undefined), /Invalid root path: path cannot be empty/);
        });
        it('should match Python test input "C:/test" -> "c:\\test"', () => {
            const path = "C:/test";
            const normalized = (0, pathNormalize_1.normalizeRootPath)(path);
            assert.strictEqual(normalized, "c:\\test");
        });
    });
    describe('computeRepoId', () => {
        it('should produce consistent SHA256 hash matching Python', () => {
            const path = "c:\\test\\path";
            const repoId1 = (0, pathNormalize_1.computeRepoId)(path);
            const repoId2 = (0, pathNormalize_1.computeRepoId)(path);
            const expectedHash = crypto.createHash('sha256').update(path, 'utf-8').digest('hex').toLowerCase();
            assert.strictEqual(repoId1, expectedHash);
            assert.strictEqual(repoId1, repoId2);
        });
        it('should return lowercase hex string', () => {
            const path = "c:\\test\\path";
            const repoId = (0, pathNormalize_1.computeRepoId)(path);
            assert.strictEqual(repoId, repoId.toLowerCase());
            assert.match(repoId, /^[a-f0-9]{64}$/);
        });
    });
});
