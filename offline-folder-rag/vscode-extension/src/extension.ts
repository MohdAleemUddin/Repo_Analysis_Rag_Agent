import * as vscode from 'vscode';
import { registerCommands } from './confluence/commands';

export function activate(context: vscode.ExtensionContext): void {
  context.subscriptions.push(
    vscode.commands.registerCommand('confluence.placeholder', () => {})
  );
  registerCommands(context);
}

export function deactivate(): void {}
