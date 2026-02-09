import * as assert from 'assert';
import * as vscode from 'vscode';
import * as path from 'path';
import { ChatPanelViewProvider } from '../../vscode-extension/src/webview/ChatPanelViewProvider';
import { readRootPath, readRecentFolders, writeRootPath } from '../../vscode-extension/src/services/storage';

// Mocking vscode and global state for testing
const mockContext = {
    globalState: {
        _data: {} as Record<string, any>,
        get(key: string, defaultValue?: any) {
            return this._data[key] ?? defaultValue;
        },
        update(key: string, value: any) {
            this._data[key] = value;
            return Promise.resolve();
        }
    },
    extensionUri: { fsPath: '/' } as vscode.Uri,
    globalStorageUri: { fsPath: '/storage' } as vscode.Uri
} as unknown as vscode.ExtensionContext;

describe('Local Dropdown Selection and Cancel Functional Test', () => {
    let provider: ChatPanelViewProvider;
    let postedMessages: any[] = [];

    beforeEach(() => {
        (mockContext.globalState as any)['_data'] = {};
        postedMessages = [];
        provider = new ChatPanelViewProvider(mockContext, mockContext.extensionUri);
        
        // Mock postMessage
        (provider as any).panel = {
            webview: {
                postMessage: (msg: any) => {
                    postedMessages.push(msg);
                    return Promise.resolve();
                },
                onDidReceiveMessage: () => ({ dispose: () => {} }),
                html: ''
            },
            reveal: () => {},
            onDidDispose: () => ({ dispose: () => {} })
        };
    });

    it('Select Folder... opens the native folder picker', async () => {
        let pickerOpened = false;
        const originalShowOpenDialog = vscode.window.showOpenDialog;
        vscode.window.showOpenDialog = async (options: any) => {
            pickerOpened = true;
            assert.strictEqual(options?.canSelectFolders, true);
            return undefined;
        };

        await (provider as any).handleWebviewMessage({ type: 'localPick' });

        assert.ok(pickerOpened, 'Folder picker should have opened');
        vscode.window.showOpenDialog = originalShowOpenDialog;
    });

    it('Cancelling the picker does not modify state (no changes to root_path or recent folders)', async () => {
        const initialRoot = path.resolve('/initial/path');
        await writeRootPath(mockContext, initialRoot);
        
        const originalShowOpenDialog = vscode.window.showOpenDialog;
        vscode.window.showOpenDialog = async () => undefined; // Simulate cancel

        await (provider as any).handleWebviewMessage({ type: 'localPick' });

        assert.strictEqual(readRootPath(mockContext), initialRoot);
        assert.deepStrictEqual(readRecentFolders(mockContext), [initialRoot]);
        
        const localStateMsg = postedMessages.filter(m => m.type === 'localState').pop();
        assert.strictEqual(localStateMsg.rootPath, initialRoot);
        assert.deepStrictEqual(localStateMsg.recentFolders, [initialRoot]);
        
        vscode.window.showOpenDialog = originalShowOpenDialog;
    });

    it('Selecting a folder updates root_path and adds to recent list (deterministic, ≤10, most recent first)', async () => {
        const selectedPath = path.resolve('/new/folder');
        const originalShowOpenDialog = vscode.window.showOpenDialog;
        vscode.window.showOpenDialog = async () => [{ fsPath: selectedPath } as vscode.Uri];

        await (provider as any).handleWebviewMessage({ type: 'localPick' });

        assert.strictEqual(readRootPath(mockContext), selectedPath);
        const recent = readRecentFolders(mockContext);
        assert.strictEqual(recent[0], selectedPath);
        assert.ok(recent.length <= 10);
        
        const localStateMsg = postedMessages.filter(m => m.type === 'localState').pop();
        assert.strictEqual(localStateMsg.rootPath, selectedPath);
        assert.strictEqual(localStateMsg.recentFolders[0], selectedPath);

        vscode.window.showOpenDialog = originalShowOpenDialog;
    });

    it('Recent folders list is deterministic (≤10 entries, most recent first)', async () => {
        for (let i = 1; i <= 15; i++) {
            await (provider as any).handleWebviewMessage({ 
                type: 'localSelect', 
                folder: path.resolve(`/path/${i}`) 
            });
        }

        const recent = readRecentFolders(mockContext);
        assert.strictEqual(recent.length, 10);
        assert.strictEqual(recent[0], path.resolve('/path/15'));
        assert.strictEqual(recent[9], path.resolve('/path/6'));
    });

    it('Recent folders render correctly in the Local dropdown below Select Folder...', async () => {
        const folders = [path.resolve('/path/A'), path.resolve('/path/B')];
        for (const f of folders) {
            await (provider as any).handleWebviewMessage({ type: 'localSelect', folder: f });
        }

        const lastState = postedMessages.filter(m => m.type === 'localState').pop();
        assert.ok(lastState, 'Should have posted localState');
        assert.strictEqual(lastState.rootPath, folders[1]);
        assert.deepStrictEqual(lastState.recentFolders, [folders[1], folders[0]]);
    });
});
