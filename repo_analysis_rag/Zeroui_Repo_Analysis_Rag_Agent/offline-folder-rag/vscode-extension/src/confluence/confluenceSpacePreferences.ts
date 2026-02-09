/**
 * Per-folder Confluence space preference (US-2).
 */

import * as path from "path";
import * as vscode from "vscode";

const CONFLUENCE_SPACE_PREFIX = "confluence.spacePreference.";

function normalizeFolder(folder: string | undefined): string {
    if (!folder) return "";
    return path.resolve(folder);
}

export function getSpacePreference(context: vscode.ExtensionContext, folderPath: string | undefined): string | undefined {
    const key = CONFLUENCE_SPACE_PREFIX + normalizeFolder(folderPath);
    return context.globalState.get<string>(key);
}

export async function setSpacePreference(context: vscode.ExtensionContext, folderPath: string | undefined, space: string): Promise<void> {
    if (!folderPath) return;
    const key = CONFLUENCE_SPACE_PREFIX + normalizeFolder(folderPath);
    await context.globalState.update(key, space);
}

export function getSuggestedSpaceFromProjectType(projectTypeLabel: string | undefined): "DEV" | "DOCS" {
    if (!projectTypeLabel) return "DEV";
    const lower = projectTypeLabel.toLowerCase();
    if (lower.includes("documentation") || lower.includes("docs") || lower === "configuration") return "DOCS";
    return "DEV";
}
