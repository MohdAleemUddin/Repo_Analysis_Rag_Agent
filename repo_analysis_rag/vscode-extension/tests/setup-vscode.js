const Module = require('module');

// Minimal mock for vscode
const vscodeMock = {
    window: {
        showInformationMessage: () => Promise.resolve(),
        showErrorMessage: () => Promise.resolve(),
        createWebviewPanel: () => ({
            webview: {
                onDidReceiveMessage: () => ({ dispose: () => {} }),
                postMessage: () => Promise.resolve(),
                html: ''
            },
            onDidDispose: () => ({ dispose: () => {} }),
            reveal: () => {},
            dispose: () => {}
        }),
        activeTextEditor: undefined
    },
    workspace: {
        workspaceFolders: [],
        getConfiguration: () => ({
            get: (key) => undefined,
            update: () => Promise.resolve()
        }),
        onDidSaveTextDocument: () => ({ dispose: () => {} })
    },
    Uri: {
        parse: (s) => ({ fsPath: s, scheme: 'file' }),
        file: (s) => ({ fsPath: s, scheme: 'file' }),
        joinPath: (uri, ...parts) => ({ fsPath: uri.fsPath + '/' + parts.join('/'), scheme: 'file' })
    },
    Range: class { constructor() {} },
    Position: class { constructor() {} },
    Selection: class { constructor() {} },
    ThemeColor: class { constructor() {} },
    EventEmitter: class { constructor() { this.event = () => {}; } },
    CancellationTokenSource: class { constructor() { this.token = {}; } }
};

// Override the require for 'vscode'
const originalRequire = Module.prototype.require;
Module.prototype.require = function (path) {
    if (path === 'vscode') {
        return vscodeMock;
    }
    return originalRequire.apply(this, arguments);
};
