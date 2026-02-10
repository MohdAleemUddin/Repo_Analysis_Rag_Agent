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
const chatPanelHtml_1 = require("../../vscode-extension/src/webview/ui/chatPanelHtml");
describe('Microphone Icon Disabled State Functional Test', () => {
    let html;
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
        };
        html = (0, chatPanelHtml_1.getChatPanelHtml)(mockUri);
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
