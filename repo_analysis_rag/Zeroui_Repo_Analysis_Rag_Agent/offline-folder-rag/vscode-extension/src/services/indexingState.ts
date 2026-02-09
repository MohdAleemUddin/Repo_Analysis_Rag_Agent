const indexingRoots = new Set<string>();

export function setIndexing(rootPath: string): void {
    indexingRoots.add(rootPath);
}

export function isIndexing(rootPath: string): boolean {
    return indexingRoots.has(rootPath);
}

export function clearIndexing(rootPath: string): void {
    indexingRoots.delete(rootPath);
}
