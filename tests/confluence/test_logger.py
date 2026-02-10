"""Tests for app.logging.logger: mask_tokens (all patterns), TokenMaskingFilter, get_logger."""

import logging


def _import_logger():
    from app.logging.logger import mask_tokens, TokenMaskingFilter, get_logger, MASK

    return mask_tokens, TokenMaskingFilter, get_logger, MASK


def test_mask_tokens_key_value_pattern():
    mask_tokens, _, _, _ = _import_logger()
    assert "***MASKED***" in mask_tokens("api_token=secret123")
    assert "***MASKED***" in mask_tokens("password=xyz")


def test_mask_tokens_bearer_pattern():
    mask_tokens, _, _, _ = _import_logger()
    out = mask_tokens("Authorization: Bearer abc.def.xyz")
    assert out == "Authorization: Bearer ***MASKED***" or "***MASKED***" in out


def test_mask_tokens_token_param_pattern():
    mask_tokens, _, _, _ = _import_logger()
    out = mask_tokens("url?token=abc123")
    assert "token=***MASKED***" in out or "***MASKED***" in out


def test_token_masking_filter_masks_msg():
    _, TokenMaskingFilter, _, _ = _import_logger()
    rec = logging.LogRecord("n", 0, "", 0, "api_token=leak", (), None)
    f = TokenMaskingFilter()
    f.filter(rec)
    assert "leak" not in str(rec.msg)
    assert "***MASKED***" in str(rec.msg)


def test_token_masking_filter_masks_args():
    _, TokenMaskingFilter, _, _ = _import_logger()
    rec = logging.LogRecord("n", 0, "", 0, "msg %s", ("Bearer tok123",), None)
    f = TokenMaskingFilter()
    f.filter(rec)
    assert "tok123" not in str(rec.args)
    assert "***MASKED***" in str(rec.args)


def test_token_masking_filter_args_non_string_unchanged():
    _, TokenMaskingFilter, _, _ = _import_logger()
    rec = logging.LogRecord("n", 0, "", 0, "count %s", (42,), None)
    f = TokenMaskingFilter()
    f.filter(rec)
    assert rec.args == (42,)


def test_get_logger_adds_filter_once():
    _, _, get_logger, _ = _import_logger()
    name = "test_logger_idempotent_xyz"
    log1 = get_logger(name)
    log2 = get_logger(name)
    filters = [f for f in log1.filters if f.__class__.__name__ == "TokenMaskingFilter"]
    assert len(filters) == 1
    assert log1 is log2
