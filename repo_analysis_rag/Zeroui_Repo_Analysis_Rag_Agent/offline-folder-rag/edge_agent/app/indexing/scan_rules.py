import os
import hashlib
from pathlib import Path
from ..security.token_store import index_dir

__all__ = ["normalize_root_path", "compute_repo_id", "scan_repository", "should_skip_path", "is_symlink_entry"]

EXCLUDED_DIRECTORIES = {
    ".git", "node_modules", ".venv", "venv", "dist", "build",
    ".pytest_cache", ".mypy_cache", ".idea", ".vscode"
}

EXCLUDED_EXTENSIONS = {
    # Images
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".ico",
    # Media
    ".mp4", ".mov", ".avi", ".mkv", ".mp3", ".wav",
    # Archives
    ".zip", ".7z", ".rar", ".tar", ".gz",
    # Executables
    ".exe", ".dll", ".so", ".dylib",
    # DB
    ".db", ".sqlite", ".sqlite3"
}

def normalize_root_path(raw_path: str) -> str:
    """Normalize a root path to a standard format."""
    if raw_path is None or raw_path == "":
        raise ValueError("Invalid root path: path cannot be empty")
    
    # Convert to absolute path
    abs_path = os.path.abspath(raw_path)
    
    # Resolve . and ..
    norm_path = os.path.normpath(abs_path)
    
    # Replace forward slashes (/) with backslashes (\)
    norm_path = norm_path.replace('/', '\\')
    
    # Remove trailing backslash except for Windows drive root (e.g., "C:\")
    if norm_path.endswith('\\') and not (len(norm_path) == 3 and norm_path[1:3] == ':\\'):
        norm_path = norm_path.rstrip('\\')
    
    # Convert entire string to lowercase
    return norm_path.lower()

def compute_repo_id(normalized_path: str) -> str:
    """Compute a unique repo ID from a normalized path."""
    return hashlib.sha256(normalized_path.encode('utf-8')).hexdigest().lower()

def scan_repository(root_path: str, mode: str = "full", changed_files: list[str] | None = None) -> dict:
    """Scan a repository and return indexing results."""
    from . import indexer
    normalized_path = normalize_root_path(root_path)
    repo_id = compute_repo_id(normalized_path)
    
    # Construct manifest path and Chroma collection names (for reference in return)
    manifest_path = index_dir() / repo_id / "manifest.json"
    code_collection = f"{repo_id}_code_chunks"
    doc_collection = f"{repo_id}_doc_chunks"
    
    if mode == "incremental" and changed_files is not None:
        results = indexer._run_incremental_index(repo_id, changed_files)
    else:
        # Perform the actual scan using the integrated logic in indexer.py
        results = indexer.perform_indexing_scan(root_path, repo_id)
    
    # Enrich results with paths and collections
    results.update({
        "manifest_path": str(manifest_path),
        "collections": [code_collection, doc_collection]
    })
    return results

def should_skip_path(root_path: str, file_path: str, is_dir: bool, max_file_size_mb: int = 5) -> bool:
    """
    Deterministic exclusion logic based on PRD §11.1-11.3.
    Returns True if the path should be skipped, False otherwise.
    """
    # 1. Boundary check: If file_path is not under root_path → return True
    try:
        # Use abspath to ensure we are comparing absolute paths
        abs_root = os.path.abspath(root_path)
        abs_file = os.path.abspath(file_path)
        
        # commonpath returns the longest common sub-path of each passed pathname.
        # If the common path is not the root path, then the file is outside the root.
        if os.path.commonpath([abs_root, abs_file]) != abs_root:
            return True
    except (ValueError, OSError):
        # Safe by default: When unsure, return True (skip)
        return True

    if is_dir:
        # 2. Directory exclusion: If is_dir and directory name matches PRD excluded list
        dir_name = os.path.basename(file_path)
        if dir_name.lower() in {d.lower() for d in EXCLUDED_DIRECTORIES}:
            return True
    else:
        # 3. File extension exclusion: If not is_dir and file extension matches PRD excluded extensions
        _, ext = os.path.splitext(file_path)
        if ext.lower() in {e.lower() for e in EXCLUDED_EXTENSIONS}:
            return True
            
        # 4. Classification-aware size cap
        # "code" and "other" use a fixed 5MB cap.
        # "docs/config" (markdown or others) use the configurable max_file_size_mb.
        
        # Simple classification logic matching chunker.py
        if ext.lower() == ".md":
            effective_max_mb = max_file_size_mb
        else:
            # For now, we treat non-markdown as "code" or "other" which have fixed 5MB cap
            effective_max_mb = 5

        try:
            # Only check size if file exists (to avoid issues with mock paths in tests)
            if os.path.exists(file_path):
                file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                if file_size_mb > effective_max_mb:
                    return True
        except OSError:
            pass

    # 5. Default: Return False for all other cases
    return False

def should_skip_path_with_reason(root_path: str, file_path: str, is_dir: bool, max_file_size_mb: int = 5) -> (bool, str | None):
    """
    Deterministic exclusion logic based on PRD §11.1-11.3.
    Returns (True, skip_reason) if the path should be skipped, (False, None) otherwise.
    """
    # 1. Boundary check: If file_path is not under root_path → return True
    try:
        # Use abspath to ensure we are comparing absolute paths
        abs_root = os.path.abspath(root_path)
        abs_file = os.path.abspath(file_path)
        
        # commonpath returns the longest common sub-path of each passed pathname.
        # If the common path is not the root path, then the file is outside the root.
        if os.path.commonpath([abs_root, abs_file]) != abs_root:
            return True, "OUT_OF_BOUNDS"
    except (ValueError, OSError):
        # Safe by default: When unsure, return True (skip)
        return True, "PATH_ERROR"

    if is_dir:
        # 2. Directory exclusion: If is_dir and directory name matches PRD excluded list
        dir_name = os.path.basename(file_path)
        if dir_name.lower() in {d.lower() for d in EXCLUDED_DIRECTORIES}:
            return True, "EXCLUDED_DIR"
    else:
        # 3. File extension exclusion: If not is_dir and file extension matches PRD excluded extensions
        _, ext = os.path.splitext(file_path)
        if ext.lower() in {e.lower() for e in EXCLUDED_EXTENSIONS}:
            return True, "EXCLUDED_EXT"
            
        # 4. Classification-aware size cap
        # "code" and "other" use a fixed 5MB cap.
        # "docs/config" (markdown or others) use the configurable max_file_size_mb.
        
        # Simple classification logic matching chunker.py
        if ext.lower() == ".md":
            effective_max_mb = max_file_size_mb
        else:
            # For now, we treat non-markdown as "code" or "other" which have fixed 5MB cap
            effective_max_mb = 5

        try:
            if os.path.exists(file_path):
                file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                if file_size_mb > effective_max_mb:
                    return True, "SIZE_CAP"
        except OSError:
            return True, "SIZE_CAP"

    # 5. Default: Return False for all other cases
    return False, None

def is_symlink_entry(path: str) -> bool:
    """
    Detects if a path is a symlink, junction, or reparse point.
    Handles Unix symlinks and Windows junctions/reparse points.
    Returns True if it's a symbolic link/junction, False otherwise.
    Does not raise exceptions for broken/dangling symlinks.
    """
    try:
        # os.path.islink handles Unix symlinks and Windows symlinks.
        # However, for Windows junctions, os.path.islink may return False 
        # depending on the Python version and link type.
        # pathlib.Path.is_symlink() also has similar behavior.
        # A more robust way on Windows is to check for reparse point attribute.
        if os.path.islink(path):
            return True
            
        if os.name == 'nt':
            import stat
            try:
                lstat_res = os.lstat(path)
                return bool(lstat_res.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
            except (AttributeError, OSError):
                return False
        return False
    except (OSError, ValueError):
        # Return False if we can't access the path or it's invalid
        return False
