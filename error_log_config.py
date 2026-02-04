"""
Configure a single .log file that records only errors (terminal and repo).
Errors are written automatically when they occur (logging.ERROR/CRITICAL and uncaught exceptions).
"""

import logging
import sys
from pathlib import Path

ERROR_LOG_PATH = Path(__file__).resolve().parent / "errors.log"
_ERROR_LOG_CONFIGURED = False


def _only_errors(record: logging.LogRecord) -> bool:
    return record.levelno >= logging.ERROR


def setup_error_log() -> None:
    """Add a file handler to the root logger that writes only ERROR and CRITICAL to errors.log."""
    global _ERROR_LOG_CONFIGURED
    if _ERROR_LOG_CONFIGURED:
        return
    try:
        handler = logging.FileHandler(ERROR_LOG_PATH, mode="a", encoding="utf-8")
        handler.setLevel(logging.ERROR)
        handler.addFilter(_only_errors)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        logging.getLogger().addHandler(handler)
        _ERROR_LOG_CONFIGURED = True
    except Exception:
        pass

    def _excepthook(etype, value, tb):
        try:
            with open(ERROR_LOG_PATH, "a", encoding="utf-8") as f:
                import traceback
                f.write("\n--- Uncaught exception ---\n")
                traceback.print_exception(etype, value, tb, file=f)
        except Exception:
            pass
        sys.__excepthook__(etype, value, tb)

    sys.excepthook = _excepthook


def append_error_line(line: str) -> None:
    """Append a single error line to errors.log (e.g. from terminal/pytest failure)."""
    try:
        with open(ERROR_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line if line.endswith("\n") else line + "\n")
    except Exception:
        pass
