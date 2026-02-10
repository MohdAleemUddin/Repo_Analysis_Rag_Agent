const Module = require('module');
const path = require('path');

const mockVscode = {
    window: {
        showInformationMessage: () => Promise.resolve(),
        showErrorMessage: () => Promise.resolve(),
        showOpenDialog: () => Promise.resolve(),
        activeTextEditor: undefined,
        createWebviewPanel: () => ({
            webview: {
                onDidReceiveMessage: () => ({ dispose: () => {} }),
                postMessage: () => Promise.resolve(),
                html: ''
            },
            reveal: () => {},
            onDidDispose: () => ({ dispose: () => {} })
        }),
        Range: class {
            constructor(startLine, startChar, endLine, endChar) {
                this.start = { line: startLine, character: startChar };
                this.end = { line: endLine, character: endChar };
            }
        },
        Selection: class {
            constructor(start, end) {
                this.start = start;
                this.end = end;
            }
        },
        TextEditorRevealType: {
            InCenter: 0
        }
    },
    workspace: {
        workspaceFolders: [],
        onDidSaveTextDocument: () => ({ dispose: () => {} }),
        openTextDocument: () => Promise.resolve({}),
        getConfiguration: () => ({
            get: () => undefined,
            update: () => Promise.resolve()
        }),
        workspaceFile: undefined
    },
    Uri: {
        file: (p) => ({ fsPath: path.resolve(p), scheme: 'file' }),
        parse: (p) => ({ fsPath: p, scheme: 'file' }),
        joinPath: (uri, ...parts) => ({ fsPath: path.join(uri.fsPath, ...parts), scheme: 'file' })
    },
    Range: class {
        constructor(startLine, startChar, endLine, endChar) {
            this.start = { line: startLine, character: startChar };
            this.end = { line: endLine, character: endChar };
        }
    },
    Selection: class {
        constructor(start, end) {
            this.start = start;
            this.end = end;
        }
    },
    TextEditorRevealType: {
        InCenter: 0
    },
    EventEmitter: class {
        constructor() {
            this.listeners = [];
        }
        event(listener) {
            this.listeners.push(listener);
            return { dispose: () => {} };
        }
        fire(data) {
            this.listeners.forEach(l => l(data));
        }
    }
};

// Intercept require('vscode')
const originalLoader = Module._load;
Module._load = function (request, parent, isMain) {
    if (request === 'vscode') {
        return mockVscode;
    }
    
    // For other modules, we need to ensure they can be resolved from the extension's node_modules
    // since the tests are located outside the extension directory.
    try {
        return originalLoader.apply(this, arguments);
    } catch (err) {
        if (err.code === 'MODULE_NOT_FOUND' && !path.isAbsolute(request) && !request.startsWith('.')) {
            try {
                const extensionNodeModules = path.join(__dirname, '..', 'node_modules', request);
                return originalLoader.call(this, extensionNodeModules, parent, isMain);
            } catch (innerErr) {
                throw err;
            }
        }
        throw err;
    }
};

module.exports = mockVscode;
