import * as path from "path";
import * as vscode from "vscode";

const ROOT_PATH_KEY = "offlineFolderRag.rootPath";
const RECENT_FOLDERS_KEY = "offlineFolderRag.recentFolders";
const MAX_RECENT_FOLDERS = 10;
const AUTO_INDEX_KEY = "offlineFolderRag.autoIndexEnabled";

function normalizeFolder(folder: string): string {
    return path.resolve(folder);
}

export function readRootPath(context: vscode.ExtensionContext): string | undefined {
    return context.globalState.get<string>(ROOT_PATH_KEY);
}

export async function writeRootPath(context: vscode.ExtensionContext, folder: string): Promise<void> {
    const normalized = normalizeFolder(folder);
    await context.globalState.update(ROOT_PATH_KEY, normalized);
    await addRecentFolder(context, normalized);
}

export function readAutoIndex(context: vscode.ExtensionContext): boolean {
    return context.globalState.get<boolean>(AUTO_INDEX_KEY, false);
}

export async function writeAutoIndex(context: vscode.ExtensionContext, enabled: boolean): Promise<void> {
    await context.globalState.update(AUTO_INDEX_KEY, enabled);
}

export function readRecentFolders(context: vscode.ExtensionContext): string[] {
    return context.globalState.get<string[]>(RECENT_FOLDERS_KEY, []);
}

async function addRecentFolder(context: vscode.ExtensionContext, folder: string): Promise<void> {
    const current = context.globalState.get<string[]>(RECENT_FOLDERS_KEY, []) ?? [];
    const normalizedFolder = normalizeFolder(folder);
    const filtered = current.filter((entry) => normalizeFolder(entry) !== normalizedFolder);
    const updated = [normalizedFolder, ...filtered].slice(0, MAX_RECENT_FOLDERS);
    await context.globalState.update(RECENT_FOLDERS_KEY, updated);
}
