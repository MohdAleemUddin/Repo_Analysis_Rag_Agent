import * as assert from 'assert';
import { getChatPanelHtml } from '../../vscode-extension/src/webview/ui/chatPanelHtml';
import * as vscode from 'vscode';

describe('Microphone Icon Disabled State Functional Test', () => {
    let html: string;

    before(() => {
        // Mock vscode.Uri
        const mockUri = {
            fsPath: '/',
            scheme: 'file',
            authority: '',
            path: '/',
            query: '',
            fragment: '',
            with: () => mockUri,
            toJSON: () => ({})
        } as unknown as vscode.Uri;

        html = getChatPanelHtml(mockUri);
    });

    it('the microphone icon is rendered disabled', () => {
        // Verify the button has the disabled attribute
        assert.ok(html.includes('id="microphone-button"'), 'Microphone button should exist in HTML');
        assert.ok(html.includes('id="microphone-button"') && html.includes('disabled'), 'Microphone button should have disabled attribute');
    });

    it('hovering shows the tooltip text "Not available" exactly', () => {
        // Verify the title attribute is exactly "Not available"
        assert.ok(html.includes('title="Not available"'), 'Tooltip text should be exactly "Not available"');
        
        // More specific check for the microphone button's title
        const micButtonRegex = /<button[^>]*id="microphone-button"[^>]*title="Not available"[^>]*>/;
        assert.ok(micButtonRegex.test(html), 'Microphone button should have title="Not available"');
    });
});
