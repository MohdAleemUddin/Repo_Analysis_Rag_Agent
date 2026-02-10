"use strict";
/**
 * Per-folder Confluence space preference (US-2).
 */
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
exports.getSpacePreference = getSpacePreference;
exports.setSpacePreference = setSpacePreference;
exports.getSuggestedSpaceFromProjectType = getSuggestedSpaceFromProjectType;
const path = __importStar(require("path"));
const CONFLUENCE_SPACE_PREFIX = "confluence.spacePreference.";
function normalizeFolder(folder) {
    if (!folder)
        return "";
    return path.resolve(folder);
}
function getSpacePreference(context, folderPath) {
    const key = CONFLUENCE_SPACE_PREFIX + normalizeFolder(folderPath);
    return context.globalState.get(key);
}
async function setSpacePreference(context, folderPath, space) {
    if (!folderPath)
        return;
    const key = CONFLUENCE_SPACE_PREFIX + normalizeFolder(folderPath);
    await context.globalState.update(key, space);
}
function getSuggestedSpaceFromProjectType(projectTypeLabel) {
    if (!projectTypeLabel)
        return "DEV";
    const lower = projectTypeLabel.toLowerCase();
    if (lower.includes("documentation") || lower.includes("docs") || lower === "configuration")
        return "DOCS";
    return "DEV";
}
