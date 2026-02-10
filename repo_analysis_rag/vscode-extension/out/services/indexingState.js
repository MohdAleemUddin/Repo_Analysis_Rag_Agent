"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.setIndexing = setIndexing;
exports.isIndexing = isIndexing;
exports.clearIndexing = clearIndexing;
const indexingRoots = new Set();
function setIndexing(rootPath) {
    indexingRoots.add(rootPath);
}
function isIndexing(rootPath) {
    return indexingRoots.has(rootPath);
}
function clearIndexing(rootPath) {
    indexingRoots.delete(rootPath);
}
