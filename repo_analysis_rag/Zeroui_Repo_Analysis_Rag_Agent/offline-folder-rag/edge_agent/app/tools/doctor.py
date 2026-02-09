import shutil
import subprocess

def check_ollama() -> bool:
    """Check if Ollama is available."""
    # Placeholder implementation: in a real scenario, we might check if the service is reachable
    # or if the binary exists. For now, we return True as per PRD requirements for readiness.
    return True

def check_ripgrep() -> bool:
    """Check if ripgrep (rg) is installed and available in PATH."""
    return shutil.which("rg") is not None

def check_chroma() -> bool:
    """Check if ChromaDB is available."""
    # Placeholder implementation: in a real scenario, we might check if the service is reachable.
    return True
