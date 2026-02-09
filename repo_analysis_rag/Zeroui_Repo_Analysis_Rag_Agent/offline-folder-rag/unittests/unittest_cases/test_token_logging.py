import pytest
import sys
import os
import logging
from pathlib import Path
from io import StringIO

repo_root = Path(__file__).resolve().parents[3]
project_root = repo_root / "offline-folder-rag"
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from edge_agent.app.logging.logger import logger  # type: ignore
from edge_agent.app.security.token_store import get_or_create_token  # type: ignore

def test_token_logging_prevention():
    # Setup log capture
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    logger.addHandler(handler)
    
    try:
        token = get_or_create_token()
        
        # Attempt to log the token
        logger.info(f"The secret token is: {token}")
        
        # Verify the token is redacted
        log_output = log_stream.getvalue()
        assert token not in log_output
        assert "[REDACTED_TOKEN]" in log_output
        
    finally:
        logger.removeHandler(handler)
