"""
Start both Confluence (8000) and RAG (8001) backends.
Run from repo root: python repo_analysis_rag/run_servers.py
Or from repo_analysis_rag: python run_servers.py
"""

import os
import subprocess
import sys
import time
from pathlib import Path

try:
    import urllib.request
except ImportError:
    urllib = None

# This file is at repo_analysis_rag/run_servers.py
REPO_ANALYSIS_RAG = Path(__file__).resolve().parent
REPO_ROOT = REPO_ANALYSIS_RAG.parent
BACKEND_CONFLUENCE = REPO_ANALYSIS_RAG / "backend_confluence"
BACKEND_RAG = REPO_ANALYSIS_RAG / "backend_rag"


def wait_for_health(url: str, timeout: float = 30.0) -> bool:
    """Poll url until 200 or timeout."""
    if urllib is None:
        return True
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=2) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(1.0)
    return False


def main() -> None:
    pass  # subprocess cwd set per backend
    python = sys.executable
    env = os.environ.copy()
    env.setdefault("CONFLUENCE_PORT", "8000")
    env.setdefault("RAG_PORT", "8001")

    proc_confluence = subprocess.Popen(
        [python, "run_server.py"],
        cwd=str(BACKEND_CONFLUENCE),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    proc_rag = subprocess.Popen(
        [python, "run_server.py"],
        cwd=str(BACKEND_RAG),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    try:
        print("Confluence: http://localhost:8000")
        print("RAG:       http://localhost:8001")
        if wait_for_health("http://localhost:8000/health") and wait_for_health(
            "http://localhost:8001/health"
        ):
            print("Both servers ready.")
        print("Press Ctrl+C to stop both.")
        proc_confluence.wait()
        proc_rag.wait()
    except KeyboardInterrupt:
        proc_confluence.terminate()
        proc_rag.terminate()
        proc_confluence.wait()
        proc_rag.wait()
        print("Stopped both servers.")


if __name__ == "__main__":
    main()
