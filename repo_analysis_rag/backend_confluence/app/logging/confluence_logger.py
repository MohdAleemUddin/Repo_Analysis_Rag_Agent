# Confluence logger (uses central logger with token masking per NFR3)
from .logger import get_logger


def get_confluence_logger():
    return get_logger("confluence")
