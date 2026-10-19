"""Log allowlist tests."""

from __future__ import annotations

import json
import logging

from diary_observability.sanitizer import JsonFormatter, sanitize


def test_canary_content_is_dropped() -> None:
    clean = sanitize(
        {
            "event": "request",
            "request_id": "r1",
            "prompt": "CANARY-DIARY-TEXT",
            "headers": {"authorization": "secret"},
            "status": 200,
        }
    )
    assert "prompt" not in clean and "headers" not in clean
    assert clean["status"] == 200


def test_formatter_outputs_json_without_canary() -> None:
    formatter = JsonFormatter("test", "1", "test")
    record = logging.LogRecord("x", logging.INFO, __file__, 1, "evt", (), None)
    record.prompt = "CANARY"
    record.operation_id = "op-1"
    rendered = formatter.format(record)
    assert "CANARY" not in rendered
    assert json.loads(rendered)["operation_id"] == "op-1"
