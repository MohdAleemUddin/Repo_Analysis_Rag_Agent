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
exports.readRootPath = readRootPath;
exports.writeRootPath = writeRootPath;
exports.readAutoIndex = readAutoIndex;
exports.writeAutoIndex = writeAutoIndex;
exports.readRecentFolders = readRecentFolders;
const path = __importStar(require("path"));
const ROOT_PATH_KEY = "offlineFolderRag.rootPath";
const RECENT_FOLDERS_KEY = "offlineFolderRag.recentFolders";
const MAX_RECENT_FOLDERS = 10;
const AUTO_INDEX_KEY = "offlineFolderRag.autoIndexEnabled";
function normalizeFolder(folder) {
    return path.resolve(folder);
}
function readRootPath(context) {
    return context.globalState.get(ROOT_PATH_KEY);
}
async function writeRootPath(context, folder) {
    const normalized = normalizeFolder(folder);
    await context.globalState.update(ROOT_PATH_KEY, normalized);
    await addRecentFolder(context, normalized);
}
function readAutoIndex(context) {
    return context.globalState.get(AUTO_INDEX_KEY, false);
}
async function writeAutoIndex(context, enabled) {
    await context.globalState.update(AUTO_INDEX_KEY, enabled);
}
function readRecentFolders(context) {
    return context.globalState.get(RECENT_FOLDERS_KEY, []);
}
async function addRecentFolder(context, folder) {
    const current = context.globalState.get(RECENT_FOLDERS_KEY, []) ?? [];
    const normalizedFolder = normalizeFolder(folder);
    const filtered = current.filter((entry) => normalizeFolder(entry) !== normalizedFolder);
    const updated = [normalizedFolder, ...filtered].slice(0, MAX_RECENT_FOLDERS);
    await context.globalState.update(RECENT_FOLDERS_KEY, updated);
}
