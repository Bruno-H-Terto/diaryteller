"""Compatibility gate: the backend never drops an existing route or method."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.export_openapi import BASELINE, export_specs

pytestmark = pytest.mark.contract

_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


def _operations(document: dict) -> set[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    for path, item in document.get("paths", {}).items():
        for method in item:
            if method.lower() in _METHODS:
                found.add((method.lower(), path))
    return found


def test_baseline_snapshots_exist() -> None:
    for service in ("identity", "conversation", "speech", "memory_mcp"):
        assert (BASELINE / f"{service}.json").is_file(), service


def test_no_route_is_removed() -> None:
    current = export_specs()
    for service, document in current.items():
        baseline = json.loads((BASELINE / f"{service}.json").read_text(encoding="utf-8"))
        removed = _operations(baseline) - _operations(document)
        assert not removed, f"{service} removed operations: {sorted(removed)}"


def test_documents_are_openapi_31() -> None:
    for document in export_specs().values():
        assert document["openapi"].startswith("3.1")


def test_generated_snapshots_match_source() -> None:
    current = export_specs()
    for service, document in current.items():
        snapshot = json.loads(Path(f"contracts/openapi/{service}.json").read_text(encoding="utf-8"))
        assert snapshot == json.loads(json.dumps(document, sort_keys=True)), service
