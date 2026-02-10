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
const commandRouter_1 = require("../../../vscode-extension/src/commands/commandRouter");
describe('Slash Command Parsing', () => {
    const mockContext = {
        globalStorageUri: { fsPath: '/tmp/storage' },
        globalState: {
            get: (key) => {
                if (key === 'offlineFolderRag.rootPath')
                    return '/mock/root';
                return undefined;
            },
            update: (key, value) => Promise.resolve()
        }
    };
    it('should return correct response for /index full', async () => {
        const result = await (0, commandRouter_1.parseSlashCommand)('/index full', mockContext);
        assert.strictEqual(result.type, 'commandResult');
        assert.strictEqual(result.payload, 'Indexing started: full scan');
    });
    it('should return correct response for /index incremental', () => {
        const result = (0, commandRouter_1.handleToolsSlashCommand)('/index incremental');
        assert.strictEqual(result, 'Indexing started: incremental scan');
    });
    it('should return correct response for /index incremental', async () => {
        const result = await (0, commandRouter_1.parseSlashCommand)('/index incremental', mockContext);
        assert.strictEqual(result.type, 'commandResult');
        assert.strictEqual(result.payload, 'Indexing started: incremental scan');
    });
    it('should return correct response for /index report', () => {
        const result = (0, commandRouter_1.handleToolsSlashCommand)('/index report');
        assert.strictEqual(result, 'Indexing started: report scan');
    });
    it('should return correct response for /index report', async () => {
        const result = await (0, commandRouter_1.parseSlashCommand)('/index report', mockContext);
        assert.ok(['commandResult', 'showIndexModal', 'assistantResponse'].includes(result.type));
    });
    it('should return correct response for /overview', () => {
        const result = (0, commandRouter_1.handleToolsSlashCommand)('/overview');
        assert.strictEqual(result, 'Overview: Folder structure and key files...');
    });
    it('should return correct response for /overview', async () => {
        const result = await (0, commandRouter_1.parseSlashCommand)('/overview', mockContext);
        assert.ok(['commandResult', 'showIndexModal', 'assistantResponse'].includes(result.type));
    });
    it('should return correct response for /search with arguments', () => {
        const result = (0, commandRouter_1.handleToolsSlashCommand)('/search my query');
        assert.strictEqual(result, 'Searching for my query');
    });
    it('should return correct response for /search with arguments', async () => {
        const result = await (0, commandRouter_1.parseSlashCommand)('/search my query', mockContext);
        assert.ok(['commandResult', 'showIndexModal', 'assistantResponse'].includes(result.type));
    });
    it('should return correct response for /doctor', async () => {
        const result = await (0, commandRouter_1.parseSlashCommand)('/doctor', mockContext);
        assert.ok(['commandResult', 'assistantResponse'].includes(result.type));
    });
    it('should return correct response for /doctor', () => {
        const result = (0, commandRouter_1.handleToolsSlashCommand)('/doctor');
        assert.strictEqual(result, 'Running system checks...');
    });
    it('should return correct response for /doctor', async () => {
        const result = await (0, commandRouter_1.parseSlashCommand)('/doctor', mockContext);
        assert.strictEqual(result.type, 'assistantResponse');
    });
    it('should return correct response for /autoindex on', () => {
        const result = (0, commandRouter_1.handleToolsSlashCommand)('/autoindex on');
        assert.strictEqual(result, 'Auto-indexing enabled');
    });
    it('should return correct response for /autoindex on', async () => {
        const result = await (0, commandRouter_1.parseSlashCommand)('/autoindex on', mockContext);
        assert.strictEqual(result.type, 'commandResult');
        assert.ok(result.payload === 'Auto-index enabled.' || result.payload === 'Root path not selected.');
    });
    it('should return correct response for /autoindex off', () => {
        const result = (0, commandRouter_1.handleToolsSlashCommand)('/autoindex off');
        assert.strictEqual(result, 'Auto-indexing disabled');
    });
    it('should return correct response for /autoindex off', async () => {
        const result = await (0, commandRouter_1.parseSlashCommand)('/autoindex off', mockContext);
        assert.strictEqual(result.type, 'commandResult');
        assert.ok(result.payload === 'Auto-index disabled.' || result.payload === 'Root path not selected.');
    });
    it('should return correct response for /ask with arguments', () => {
        const result = (0, commandRouter_1.handleToolsSlashCommand)('/ask how do I use this?');
        assert.strictEqual(result, 'Asking the system: how do I use this?');
    });
    it('should return correct response for /ask with arguments', async () => {
        const result = await (0, commandRouter_1.parseSlashCommand)('/ask how do I use this?', mockContext);
        assert.ok(['commandResult', 'showIndexModal', 'assistantResponse'].includes(result.type));
    });
    it('should return INVALID_COMMAND for unknown commands', () => {
        const result = (0, commandRouter_1.handleToolsSlashCommand)('/unknown');
        assert.strictEqual(result, 'INVALID_COMMAND');
    });
    it('should return INVALID_COMMAND for unknown commands', async () => {
        const result = await (0, commandRouter_1.parseSlashCommand)('/unknown', mockContext);
        assert.strictEqual(result.type, 'commandResult');
        assert.strictEqual(result.payload, 'INVALID_COMMAND');
    });
    it('should handle trailing spaces', () => {
        const result = (0, commandRouter_1.handleToolsSlashCommand)('/overview  ');
        assert.strictEqual(result, 'Overview: Folder structure and key files...');
    });
    it('should handle trailing spaces', async () => {
        const result = await (0, commandRouter_1.parseSlashCommand)('/overview  ', mockContext);
        assert.ok(['commandResult', 'showIndexModal', 'assistantResponse'].includes(result.type));
    });
});
