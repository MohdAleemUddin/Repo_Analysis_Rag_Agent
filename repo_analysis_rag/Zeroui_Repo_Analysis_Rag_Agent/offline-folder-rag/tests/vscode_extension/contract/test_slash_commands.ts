import * as assert from 'assert';
import * as vscode from 'vscode';
import { parseSlashCommand, handleToolsSlashCommand } from '../../../vscode-extension/src/commands/commandRouter';

describe('Slash Command Parsing', () => {
    const mockContext = {
        globalStorageUri: { fsPath: '/tmp/storage' },
        globalState: {
            get: (key) => {
                if (key === 'offlineFolderRag.rootPath') return '/mock/root';
                return undefined;
            },
            update: (key, value) => Promise.resolve()
        }
    } as unknown as vscode.ExtensionContext;

    it('should return correct response for /index full', async () => {
        const result = await parseSlashCommand('/index full', mockContext);
        assert.strictEqual(result.type, 'commandResult');
        assert.strictEqual(result.payload, 'Indexing started: full scan');
    });

    it('should return correct response for /index incremental', () => {
        const result = handleToolsSlashCommand('/index incremental');
        assert.strictEqual(result, 'Indexing started: incremental scan');
    });
    it('should return correct response for /index incremental', async () => {
        const result = await parseSlashCommand('/index incremental', mockContext);
        assert.strictEqual(result.type, 'commandResult');
        assert.strictEqual(result.payload, 'Indexing started: incremental scan');
    });

    it('should return correct response for /index report', () => {
        const result = handleToolsSlashCommand('/index report');
        assert.strictEqual(result, 'Indexing started: report scan');
    });
    it('should return correct response for /index report', async () => {
        const result = await parseSlashCommand('/index report', mockContext);
        assert.ok(['commandResult', 'showIndexModal', 'assistantResponse'].includes(result.type));
    });

    it('should return correct response for /overview', () => {
        const result = handleToolsSlashCommand('/overview');
        assert.strictEqual(result, 'Overview: Folder structure and key files...');
    });
    it('should return correct response for /overview', async () => {
        const result = await parseSlashCommand('/overview', mockContext);
        assert.ok(['commandResult', 'showIndexModal', 'assistantResponse'].includes(result.type));
    });

    it('should return correct response for /search with arguments', () => {
        const result = handleToolsSlashCommand('/search my query');
        assert.strictEqual(result, 'Searching for my query');
    });
    it('should return correct response for /search with arguments', async () => {
        const result = await parseSlashCommand('/search my query', mockContext);
        assert.ok(['commandResult', 'showIndexModal', 'assistantResponse'].includes(result.type));
    });

    it('should return correct response for /doctor', async () => {
        const result = await parseSlashCommand('/doctor', mockContext);
        assert.ok(['commandResult', 'assistantResponse'].includes(result.type));
    });

    it('should return correct response for /doctor', () => {
        const result = handleToolsSlashCommand('/doctor');
        assert.strictEqual(result, 'Running system checks...');
    });
    it('should return correct response for /doctor', async () => {
        const result = await parseSlashCommand('/doctor', mockContext);
        assert.strictEqual(result.type, 'assistantResponse');
    });

    it('should return correct response for /autoindex on', () => {
        const result = handleToolsSlashCommand('/autoindex on');
        assert.strictEqual(result, 'Auto-indexing enabled');
    });
    it('should return correct response for /autoindex on', async () => {
        const result = await parseSlashCommand('/autoindex on', mockContext);
        assert.strictEqual(result.type, 'commandResult');
        assert.ok(result.payload === 'Auto-index enabled.' || result.payload === 'Root path not selected.');
    });

    it('should return correct response for /autoindex off', () => {
        const result = handleToolsSlashCommand('/autoindex off');
        assert.strictEqual(result, 'Auto-indexing disabled');
    });
    it('should return correct response for /autoindex off', async () => {
        const result = await parseSlashCommand('/autoindex off', mockContext);
        assert.strictEqual(result.type, 'commandResult');
        assert.ok(result.payload === 'Auto-index disabled.' || result.payload === 'Root path not selected.');
    });

    it('should return correct response for /ask with arguments', () => {
        const result = handleToolsSlashCommand('/ask how do I use this?');
        assert.strictEqual(result, 'Asking the system: how do I use this?');
    });
    it('should return correct response for /ask with arguments', async () => {
        const result = await parseSlashCommand('/ask how do I use this?', mockContext);
        assert.ok(['commandResult', 'showIndexModal', 'assistantResponse'].includes(result.type));
    });

    it('should return INVALID_COMMAND for unknown commands', () => {
        const result = handleToolsSlashCommand('/unknown');
        assert.strictEqual(result, 'INVALID_COMMAND');
    });
    it('should return INVALID_COMMAND for unknown commands', async () => {
        const result = await parseSlashCommand('/unknown', mockContext);
        assert.strictEqual(result.type, 'commandResult');
        assert.strictEqual(result.payload, 'INVALID_COMMAND');
    });

    it('should handle trailing spaces', () => {
        const result = handleToolsSlashCommand('/overview  ');
        assert.strictEqual(result, 'Overview: Folder structure and key files...');
    });
    it('should handle trailing spaces', async () => {
        const result = await parseSlashCommand('/overview  ', mockContext);
        assert.ok(['commandResult', 'showIndexModal', 'assistantResponse'].includes(result.type));
    });
});
