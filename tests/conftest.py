"""Pytest configuration. Add edge_agent to path so app package is importable. Errors go to errors.log."""

import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
edge_agent = root / "offline-folder-rag" / "edge_agent"
if str(edge_agent) not in sys.path:
    sys.path.insert(0, str(edge_agent))

try:
    from error_log_config import setup_error_log, append_error_line, ERROR_LOG_PATH
except ImportError:
    ERROR_LOG_PATH = root / "errors.log"
    def setup_error_log(): pass
    def append_error_line(_): pass


def pytest_configure(config):
    setup_error_log()


def pytest_exception_interact(node, call, report):
    """When a test fails or errors, append the failure text to errors.log."""
    if report.failed and getattr(report, "longreprtext", None):
        try:
            with open(ERROR_LOG_PATH, "a", encoding="utf-8") as f:
                f.write("\n--- Test failure ---\n")
                f.write(report.longreprtext)
                if not report.longreprtext.endswith("\n"):
                    f.write("\n")
        except Exception:
            pass
