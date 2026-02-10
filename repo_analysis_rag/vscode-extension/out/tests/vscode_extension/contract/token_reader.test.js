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
const fs = __importStar(require("fs"));
const os = __importStar(require("os"));
const path = __importStar(require("path"));
const agentClient_1 = require("../../../vscode-extension/src/services/agentClient");
async function withTempDir(run) {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "token-reader-"));
    try {
        await run(dir);
    }
    finally {
        fs.rmSync(dir, { recursive: true, force: true });
    }
}
describe("agentClient token reading", () => {
    const originalEnv = { ...process.env };
    afterEach(() => {
        process.env = { ...originalEnv };
    });
    it("reads token using RAG_INDEX_DIR path", async () => {
        await withTempDir(async (tempDir) => {
            process.env.RAG_INDEX_DIR = tempDir;
            const tokenPath = (0, agentClient_1.getTokenFilePath)();
            fs.mkdirSync(path.dirname(tokenPath), { recursive: true });
            fs.writeFileSync(tokenPath, "abc123", "utf8");
            const token = (0, agentClient_1.readAgentToken)();
            assert.strictEqual(token, "abc123");
        });
    });
    it("falls back to USERPROFILE/.offline_rag_index", async () => {
        await withTempDir(async (tempDir) => {
            delete process.env.RAG_INDEX_DIR;
            process.env.USERPROFILE = tempDir;
            const tokenPath = (0, agentClient_1.getTokenFilePath)();
            fs.mkdirSync(path.dirname(tokenPath), { recursive: true });
            fs.writeFileSync(tokenPath, "from_profile", "utf8");
            const token = (0, agentClient_1.readAgentToken)();
            assert.strictEqual(token, "from_profile");
            assert.ok(tokenPath.startsWith(tempDir));
        });
    });
});
