"""Pytest configuration. Add backend_confluence and backend_rag to path so app package is importable. Errors go to errors.log."""

import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
backend_confluence = root / "repo_analysis_rag" / "backend_confluence"
backend_rag = root / "repo_analysis_rag" / "backend_rag"
# Insert backend_rag first so backend_confluence ends up at index 0; tests need app.* from confluence
for path in (backend_rag, backend_confluence):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

try:
    from error_log_config import setup_error_log, append_error_line, ERROR_LOG_PATH
except ImportError:
    ERROR_LOG_PATH = root / "errors.log"

    def setup_error_log():
        pass

    def append_error_line(_):
        pass


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
