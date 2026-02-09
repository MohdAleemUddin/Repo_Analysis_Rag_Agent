import json
import os
from pathlib import Path
from ..security.token_store import index_dir

class ConfigStore:
    """Legacy class to support existing tests."""
    ALLOWED_MAX_FILE_SIZE_MB = {5, 10, 20}

    def __init__(self, config_dict: dict = None):
        self.max_file_size_mb = 5
        self.chunk_size = 1000
        self.chunk_overlap = 200
        
        if config_dict:
            val = config_dict.get("max_file_size_mb", 5)
            if val not in self.ALLOWED_MAX_FILE_SIZE_MB:
                raise ValueError(f"max_file_size_mb must be one of {self.ALLOWED_MAX_FILE_SIZE_MB}")
            self.max_file_size_mb = val

class RepoConfigStore:
    DEFAULT_MAX_FILES = 2000

    def get_max_files_per_incremental_run(self, repo_id: str) -> int:
        """
        Read max_files_per_incremental_run from repo config.
        Config location: {RAG_INDEX_DIR}/{repo_id}/config.json
        """
        config_path = index_dir() / repo_id / "config.json"
        if not config_path.exists():
            return self.DEFAULT_MAX_FILES
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                val = data.get("max_files_per_incremental_run")
                if isinstance(val, int) and val > 0:
                    return val
        except (json.JSONDecodeError, OSError):
            pass
            
        return self.DEFAULT_MAX_FILES
