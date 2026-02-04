"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = require("vscode");
function activate(context) {
    // Register comm
    context.subscriptions.push(vscode.commands.registerCommand('confluence.saveToIntelligent', () => {
        vscode.window.showInformationMessage('Starting chat-only Confluence flow...');
        // In a real implementation, this would trigger the UI in the chat view
    }), vscode.commands.registerCommand('confluence.saveSelection', () => {
        const selection = vscode.window.activeTextEditor?.selection;
        if (selection && !selection.isEmpty) {
            vscode.window.showInformationMessage('Saving selection to Confluence...');
        }
    }), vscode.commands.registerCommand('confluence.documentProject', () => {
        vscode.window.showInformationMessage('Documenting project intelligently...');
    }), vscode.commands.registerCommand('confluence.viewCreations', () => {
        vscode.window.showInformationMessage('Opening Intelligent Creations dashboard...');
    }), vscode.commands.registerCommand('confluence.configureSettings', () => {
        vscode.commands.executeCommand('workbench.action.openSettings', 'confluence');
    }));
    // Placeholder for chat-only UI integration
    // In the real RAG extension, this would be where we hook into the chat input area
    console.log('Confluence Chat-Only Integration activated');
}
function deactivate() { }
