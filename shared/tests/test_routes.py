"""Compatibility gate: public operations are never removed."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.contract

SERVICES = ("identity", "conversation", "memory_mcp", "exchange")
METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}
BASELINE = Path(__file__).resolve().parents[2] / "contracts" / "routes.json"


def _specs() -> dict[str, dict]:
    documents: dict[str, dict] = {}
    for service in SERVICES:
        module = importlib.import_module(f"{service}.app")
        documents[service] = module.create_app().openapi()
    return documents


def _operations(document: dict) -> set[str]:
    return {
        f"{method} {path}"
        for path, item in document.get("paths", {}).items()
        for method in item
        if method.lower() in METHODS
    }


def test_no_public_operation_is_removed() -> None:
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    for service, document in _specs().items():
        removed = set(baseline.get(service, [])) - _operations(document)
        assert not removed, f"{service} removed: {sorted(removed)}"


def test_documents_are_openapi_31() -> None:
    for document in _specs().values():
        assert document["openapi"].startswith("3.1")
