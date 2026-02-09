const Module = require('module');

const mockVscode = {
  workspace: {
    workspaceFolders: [],
    getConfiguration: () => ({
      get: () => undefined,
      update: () => Promise.resolve(),
    }),
  },
  window: {
    showInformationMessage: () => Promise.resolve(),
    showErrorMessage: () => Promise.resolve(),
    createWebviewPanel: () => ({
      webview: {
        onDidReceiveMessage: () => ({ dispose: () => {} }),
        postMessage: () => Promise.resolve(),
        html: '',
      },
      onDidDispose: () => ({ dispose: () => {} }),
      reveal: () => {},
      dispose: () => {},
    }),
  },
  Uri: {
    file: (path) => ({ fsPath: path, scheme: 'file' }),
    parse: (path) => ({ fsPath: path, scheme: 'file' }),
  },
  EventEmitter: class {
    constructor() { this.event = () => ({ dispose: () => {} }); }
    fire() {}
  },
  ViewColumn: { One: 1, Two: 2 },
};

const originalRequire = Module.prototype.require;
Module.prototype.require = function(id) {
  if (id === 'vscode') {
    return mockVscode;
  }
  return originalRequire.apply(this, arguments);
};
