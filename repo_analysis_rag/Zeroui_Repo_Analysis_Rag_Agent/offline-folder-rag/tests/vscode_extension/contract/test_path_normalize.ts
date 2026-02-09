import * as assert from 'assert';
import * as crypto from 'crypto';
import { normalizeRootPath, computeRepoId } from '../../../vscode-extension/src/utils/pathNormalize';

describe('Path Normalization and Repo ID Contract Tests', () => {
    describe('normalizeRootPath', () => {
        it('should normalize basic paths with relative segments', () => {
            const path = "C:/test/../test";
            const normalized = normalizeRootPath(path);
            assert.strictEqual(normalized.endsWith('test'), true);
            assert.strictEqual(normalized.includes('/'), false);
            assert.strictEqual(normalized, normalized.toLowerCase());
        });

        it('should replace forward slashes with backslashes and remove trailing slash', () => {
            const path = "C:/users/test/folder/";
            const normalized = normalizeRootPath(path);
            assert.strictEqual(normalized.includes('\\'), true);
            assert.strictEqual(normalized.endsWith('\\'), false);
            assert.strictEqual(normalized, normalized.toLowerCase());
        });

        it('should preserve backslash for Windows drive root', () => {
            const path = "C:/";
            const normalized = normalizeRootPath(path);
            assert.strictEqual(normalized, "c:\\");
        });

        it('should throw error for empty or null input', () => {
            assert.throws(() => normalizeRootPath(""), /Invalid root path: path cannot be empty/);
            assert.throws(() => normalizeRootPath(null as any), /Invalid root path: path cannot be empty/);
            assert.throws(() => normalizeRootPath(undefined as any), /Invalid root path: path cannot be empty/);
        });

        it('should match Python test input "C:/test" -> "c:\\test"', () => {
            const path = "C:/test";
            const normalized = normalizeRootPath(path);
            assert.strictEqual(normalized, "c:\\test");
        });
    });

    describe('computeRepoId', () => {
        it('should produce consistent SHA256 hash matching Python', () => {
            const path = "c:\\test\\path";
            const repoId1 = computeRepoId(path);
            const repoId2 = computeRepoId(path);
            
            const expectedHash = crypto.createHash('sha256').update(path, 'utf-8').digest('hex').toLowerCase();
            assert.strictEqual(repoId1, expectedHash);
            assert.strictEqual(repoId1, repoId2);
        });

        it('should return lowercase hex string', () => {
            const path = "c:\\test\\path";
            const repoId = computeRepoId(path);
            assert.strictEqual(repoId, repoId.toLowerCase());
            assert.match(repoId, /^[a-f0-9]{64}$/);
        });
    });
});
