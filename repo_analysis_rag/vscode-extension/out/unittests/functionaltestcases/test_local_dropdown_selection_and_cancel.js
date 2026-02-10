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
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
const ChatPanelViewProvider_1 = require("../../vscode-extension/src/webview/ChatPanelViewProvider");
const storage_1 = require("../../vscode-extension/src/services/storage");
// Mocking vscode and global state for testing
const mockContext = {
    globalState: {
        _data: {},
        get(key, defaultValue) {
            return this._data[key] ?? defaultValue;
        },
        update(key, value) {
            this._data[key] = value;
            return Promise.resolve();
        }
    },
    extensionUri: { fsPath: '/' },
    globalStorageUri: { fsPath: '/storage' }
};
describe('Local Dropdown Selection and Cancel Functional Test', () => {
    let provider;
    let postedMessages = [];
    beforeEach(() => {
        mockContext.globalState['_data'] = {};
        postedMessages = [];
        provider = new ChatPanelViewProvider_1.ChatPanelViewProvider(mockContext, mockContext.extensionUri);
        // Mock postMessage
        provider.panel = {
            webview: {
                postMessage: (msg) => {
                    postedMessages.push(msg);
                    return Promise.resolve();
                },
                onDidReceiveMessage: () => ({ dispose: () => { } }),
                html: ''
            },
            reveal: () => { },
            onDidDispose: () => ({ dispose: () => { } })
        };
    });
    it('Select Folder... opens the native folder picker', async () => {
        let pickerOpened = false;
        const originalShowOpenDialog = vscode.window.showOpenDialog;
        vscode.window.showOpenDialog = async (options) => {
            pickerOpened = true;
            assert.strictEqual(options?.canSelectFolders, true);
            return undefined;
        };
        await provider.handleWebviewMessage({ type: 'localPick' });
        assert.ok(pickerOpened, 'Folder picker should have opened');
        vscode.window.showOpenDialog = originalShowOpenDialog;
    });
    it('Cancelling the picker does not modify state (no changes to root_path or recent folders)', async () => {
        const initialRoot = path.resolve('/initial/path');
        await (0, storage_1.writeRootPath)(mockContext, initialRoot);
        const originalShowOpenDialog = vscode.window.showOpenDialog;
        vscode.window.showOpenDialog = async () => undefined; // Simulate cancel
        await provider.handleWebviewMessage({ type: 'localPick' });
        assert.strictEqual((0, storage_1.readRootPath)(mockContext), initialRoot);
        assert.deepStrictEqual((0, storage_1.readRecentFolders)(mockContext), [initialRoot]);
        const localStateMsg = postedMessages.filter(m => m.type === 'localState').pop();
        assert.strictEqual(localStateMsg.rootPath, initialRoot);
        assert.deepStrictEqual(localStateMsg.recentFolders, [initialRoot]);
        vscode.window.showOpenDialog = originalShowOpenDialog;
    });
    it('Selecting a folder updates root_path and adds to recent list (deterministic, ≤10, most recent first)', async () => {
        const selectedPath = path.resolve('/new/folder');
        const originalShowOpenDialog = vscode.window.showOpenDialog;
        vscode.window.showOpenDialog = async () => [{ fsPath: selectedPath }];
        await provider.handleWebviewMessage({ type: 'localPick' });
        assert.strictEqual((0, storage_1.readRootPath)(mockContext), selectedPath);
        const recent = (0, storage_1.readRecentFolders)(mockContext);
        assert.strictEqual(recent[0], selectedPath);
        assert.ok(recent.length <= 10);
        const localStateMsg = postedMessages.filter(m => m.type === 'localState').pop();
        assert.strictEqual(localStateMsg.rootPath, selectedPath);
        assert.strictEqual(localStateMsg.recentFolders[0], selectedPath);
        vscode.window.showOpenDialog = originalShowOpenDialog;
    });
    it('Recent folders list is deterministic (≤10 entries, most recent first)', async () => {
        for (let i = 1; i <= 15; i++) {
            await provider.handleWebviewMessage({
                type: 'localSelect',
                folder: path.resolve(`/path/${i}`)
            });
        }
        const recent = (0, storage_1.readRecentFolders)(mockContext);
        assert.strictEqual(recent.length, 10);
        assert.strictEqual(recent[0], path.resolve('/path/15'));
        assert.strictEqual(recent[9], path.resolve('/path/6'));
    });
    it('Recent folders render correctly in the Local dropdown below Select Folder...', async () => {
        const folders = [path.resolve('/path/A'), path.resolve('/path/B')];
        for (const f of folders) {
            await provider.handleWebviewMessage({ type: 'localSelect', folder: f });
        }
        const lastState = postedMessages.filter(m => m.type === 'localState').pop();
        assert.ok(lastState, 'Should have posted localState');
        assert.strictEqual(lastState.rootPath, folders[1]);
        assert.deepStrictEqual(lastState.recentFolders, [folders[1], folders[0]]);
    });
});
