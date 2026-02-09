import logging
import re
from ..security.token_store import get_or_create_token

class TokenFilter(logging.Filter):
    def filter(self, record):
        token = get_or_create_token()
        if isinstance(record.msg, str):
            record.msg = record.msg.replace(token, "[REDACTED_TOKEN]")
        return True

def setup_logger():
    logger = logging.getLogger("edge_agent")
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logger.addFilter(TokenFilter())
    logger.addHandler(handler)
    
    return logger

logger = setup_logger()
