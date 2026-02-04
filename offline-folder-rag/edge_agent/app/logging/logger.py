# Logger with token masking (NFR3: API tokens never appear in logs)
import logging
import re

MASK = "***MASKED***"
_token_pattern = re.compile(r"(api[_-]?token|password|secret|auth)\s*[=:]\s*[\w\-]+", re.I)


def mask_tokens(msg: str) -> str:
    """Mask API tokens and secrets in log messages (NFR3)."""
    return _token_pattern.sub(r"\1=***MASKED***", msg)


class TokenMaskingFilter(logging.Filter):
    """Filter that masks tokens in log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = mask_tokens(str(record.msg))
        if record.args:
            record.args = tuple(mask_tokens(str(a)) if isinstance(a, str) else a for a in record.args)
        return True


def get_logger(name: str) -> logging.Logger:
    """Return logger with token-masking filter."""
    log = logging.getLogger(name)
    if not any(isinstance(f, TokenMaskingFilter) for f in log.filters):
        log.addFilter(TokenMaskingFilter())
    return log
