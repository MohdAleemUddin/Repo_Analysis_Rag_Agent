import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext): void {
  context.subscriptions.push(
    vscode.commands.registerCommand('confluence.placeholder', () => {})
  );
}

export function deactivate(): void {}
