"""Tests for app.confluence.export_import."""

import json
import os
import tempfile
from unittest.mock import patch

try:
    from app.confluence import export_import
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(
        0,
        str(
            Path(__file__).resolve().parents[2]
            / "repo_analysis_rag"
            / "backend_confluence"
        ),
    )
    from app.confluence import export_import


def test_strip_sensitive_data_dict():
    out = export_import._strip_sensitive_data(
        {"file_contents": "x", "template_id": "t"}
    )
    assert "file_contents" not in out
    assert out["template_id"] == "t"


def test_strip_sensitive_data_list():
    out = export_import._strip_sensitive_data([{"user_id": "u", "a": 1}])
    assert out[0]["a"] == 1
    assert "user_id" not in out[0]


def test_strip_sensitive_data_other():
    assert export_import._strip_sensitive_data("x") == "x"


def test_load_schema_no_file():
    with patch("os.path.isfile", return_value=False):
        s = export_import._load_schema()
    assert "required" in s
    assert "examples" in s.get("required", [])


def test_load_schema_with_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(
            {
                "required": ["version", "examples"],
                "definitions": {"example": {"required": ["content_profile"]}},
            },
            f,
        )
        path = f.name
    try:
        with patch("app.confluence.export_import._EXPORT_FORMAT_PATH", path):
            s = export_import._load_schema()
        assert "definitions" in s
    finally:
        os.unlink(path)


def test_validate_export_payload_missing_required():
    errs = export_import._validate_export_payload(
        {"examples": []}, {"required": ["version", "exported_at", "examples"]}
    )
    assert any("version" in e or "exported_at" in e for e in errs)


def test_validate_export_payload_examples_not_list():
    errs = export_import._validate_export_payload(
        {"version": 1, "exported_at": "x", "examples": "not-list"}, {}
    )
    assert any("array" in e for e in errs)


def test_validate_export_payload_example_not_dict():
    errs = export_import._validate_export_payload(
        {"version": 1, "exported_at": "x", "examples": ["not-dict"]},
        {
            "definitions": {
                "example": {
                    "required": [
                        "content_profile",
                        "template_ref",
                        "intelligence_metrics",
                    ]
                }
            }
        },
    )
    assert any("object" in e for e in errs)


def test_validate_export_payload_example_missing_field():
    errs = export_import._validate_export_payload(
        {"version": 1, "exported_at": "x", "examples": [{}]},
        {"definitions": {"example": {"required": ["content_profile", "template_ref"]}}},
    )
    assert len(errs) >= 1


def test_validate_export_payload_template_ref_invalid():
    errs = export_import._validate_export_payload(
        {
            "version": 1,
            "exported_at": "x",
            "examples": [
                {"content_profile": {}, "template_ref": {}, "intelligence_metrics": {}}
            ],
        },
        {
            "definitions": {
                "example": {
                    "required": [
                        "content_profile",
                        "template_ref",
                        "intelligence_metrics",
                    ]
                }
            }
        },
    )
    assert any("template_id" in e or "template_name" in e for e in errs)


def test_export_examples_basic():
    with patch.object(export_import, "get_examples", return_value=[]) as m:
        out = export_import.export_examples()
    m.assert_called_once()
    data = json.loads(out)
    assert data["version"] == 1
    assert "exported_at" in data
    assert data["examples"] == []


def test_export_examples_with_confidence_and_embedding():
    ex = {
        "content_profile": {"lang": "py"},
        "template_ref": {"template_id": "t1", "template_name": "T1"},
        "intelligence_metrics": {},
        "confidence_score": 0.85,
        "user_feedback": 4,
        "intelligence_embedding": [0.1] * 1536,
        "learned_at": "2020-01-01T00:00:00",
        "content_profile_hash": "abc",
    }
    with patch.object(export_import, "get_examples", return_value=[ex]):
        out = export_import.export_examples()
    data = json.loads(out)
    assert len(data["examples"]) == 1
    assert data["examples"][0]["confidence_score"] == 0.85
    assert data["examples"][0]["user_feedback"] == 4
    assert len(data["examples"][0]["intelligence_embedding"]) == 1536


def test_export_examples_embedding_wrong_length_dropped():
    ex = {
        "content_profile": {},
        "template_ref": {"template_id": "t", "template_name": "T"},
        "intelligence_metrics": {},
        "intelligence_embedding": [0.0] * 100,
    }
    with patch.object(export_import, "get_examples", return_value=[ex]):
        out = export_import.export_examples()
    data = json.loads(out)
    assert data["examples"][0]["intelligence_embedding"] is None


def test_validate_import_payload_invalid_json():
    ok, lst, err = export_import.validate_import_payload("not json {")
    assert ok is False
    assert lst is None
    assert "JSON" in (err or "")


def test_validate_import_payload_not_dict():
    ok, lst, err = export_import.validate_import_payload("[]")
    assert ok is False
    assert "object" in (err or "")


def test_validate_import_payload_missing_required():
    ok, lst, err = export_import.validate_import_payload({"examples": []})
    assert ok is False
    assert err is not None


def test_validate_import_payload_valid():
    payload = {
        "version": 1,
        "exported_at": "2020-01-01T00:00:00",
        "examples": [
            {
                "content_profile": {},
                "template_ref": {"template_id": "t", "template_name": "T"},
                "intelligence_metrics": {},
            }
        ],
    }
    ok, lst, err = export_import.validate_import_payload(payload)
    assert ok is True
    assert err is None
    assert len(lst) == 1


def test_import_examples_invalid_returns_zero():
    n, msg = export_import.import_examples("invalid")
    assert n == 0
    assert "Invalid" in msg or "format" in msg.lower()


def test_import_examples_empty_list():
    n, msg = export_import.import_examples(
        {"version": 1, "exported_at": "2020-01-01T00:00:00", "examples": []}
    )
    assert n == 0
    assert "0 new" in msg


def test_import_examples_valid_file_based():
    with tempfile.TemporaryDirectory() as tmp:
        payload = {
            "version": 1,
            "exported_at": "2020-01-01T00:00:00",
            "examples": [
                {
                    "content_profile": {"lang": "py"},
                    "template_ref": {"template_id": "t1", "template_name": "T1"},
                    "intelligence_metrics": {},
                }
            ],
        }
        n, msg = export_import.import_examples(payload, examples_base_dir=tmp)
    assert n == 1
    assert "1 new" in msg


def test_import_examples_merge_skips_duplicate():
    with tempfile.TemporaryDirectory() as tmp:
        payload = {
            "version": 1,
            "exported_at": "2020-01-01T00:00:00",
            "examples": [
                {
                    "content_profile": {"x": 1},
                    "template_ref": {"template_id": "t", "template_name": "T"},
                    "intelligence_metrics": {},
                },
                {
                    "content_profile": {"x": 1},
                    "template_ref": {"template_id": "t", "template_name": "T"},
                    "intelligence_metrics": {},
                },
            ],
        }
        n, _ = export_import.import_examples(payload, merge=True, examples_base_dir=tmp)
    assert n == 1


def test_export_legacy():
    with patch.object(export_import, "export_examples", return_value="{}") as m:
        out = export_import.export(None)
    m.assert_called_once()
    assert out == "{}"


def test_export_examples_metrics_confidence_score():
    ex = {
        "content_profile": {},
        "template_ref": {"template_id": "t", "template_name": "T"},
        "intelligence_metrics": {"other": 1},
        "confidence_score": 0.9,
        "learned_at": "2020-01-01",
    }
    with patch.object(export_import, "get_examples", return_value=[ex]):
        out = export_import.export_examples()
    data = json.loads(out)
    assert data["examples"][0]["intelligence_metrics"].get("confidence_score") == 0.9


def test_export_examples_user_feedback_non_int_dropped():
    ex = {
        "content_profile": {},
        "template_ref": {"template_id": "t", "template_name": "T"},
        "intelligence_metrics": {},
        "user_feedback": "4",
    }
    with patch.object(export_import, "get_examples", return_value=[ex]):
        out = export_import.export_examples()
    data = json.loads(out)
    assert data["examples"][0].get("user_feedback") is None


def test_import_examples_existing_hashes_exception():
    with tempfile.TemporaryDirectory() as tmp:
        with patch.object(
            export_import, "_get_file_examples", side_effect=Exception("read fail")
        ):
            payload = {
                "version": 1,
                "exported_at": "2020-01-01",
                "examples": [
                    {
                        "content_profile": {"a": 1},
                        "template_ref": {"template_id": "t", "template_name": "T"},
                        "intelligence_metrics": {},
                    }
                ],
            }
            n, msg = export_import.import_examples(payload, examples_base_dir=tmp)
    assert n >= 0


def test_import_examples_user_feedback_invalid():
    with tempfile.TemporaryDirectory() as tmp:
        payload = {
            "version": 1,
            "exported_at": "2020-01-01",
            "examples": [
                {
                    "content_profile": {"b": 1},
                    "template_ref": {"template_id": "t", "template_name": "T"},
                    "intelligence_metrics": {},
                    "user_feedback": 10,
                }
            ],
        }
        n, msg = export_import.import_examples(payload, examples_base_dir=tmp)
    assert n >= 0
