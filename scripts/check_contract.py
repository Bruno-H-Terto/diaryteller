"""Validate exported OpenAPI snapshots and the Android delta examples.

Checks are structural: OpenAPI 3.1 validity, unique operation ids and JSON Schema
Draft 2020-12 validation of the supplied synthetic examples. `--require-delta`
also fails when a delta operation is not implemented by the current services.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from openapi_spec_validator import validate
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOTS = ROOT / "contracts" / "openapi"
DELTA = ROOT / "contracts" / "android-delta" / "openapi.json"
EXAMPLES = DELTA.parent / "examples"
METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _operations(document: dict) -> set[tuple[str, str]]:
    return {
        (method, path)
        for path, item in document.get("paths", {}).items()
        for method in item
        if method.lower() in METHODS
    }


def validate_snapshots() -> list[str]:
    """Validate every exported service snapshot and its operation ids."""
    errors: list[str] = []
    for path in sorted(SNAPSHOTS.glob("*.json")):
        document = _load(path)
        try:
            validate(document)
        except Exception as exc:
            errors.append(f"{path.name}: invalid OpenAPI: {exc}")
            continue
        operation_ids = [
            item[method].get("operationId")
            for item in document["paths"].values()
            for method in item
            if method in METHODS
        ]
        if len(operation_ids) != len(set(operation_ids)):
            errors.append(f"{path.name}: duplicate operationId")
        if not path.name.endswith(".json") or len(document["paths"]) == 0:
            errors.append(f"{path.name}: no paths")
    return errors


def _registry(document: dict) -> tuple[Registry, str]:
    uri = "urn:diary:android-delta"
    resource = Resource(contents=document, specification=DRAFT202012)
    return Registry().with_resource(uri, resource), uri


def validate_examples() -> list[str]:
    """Validate every mapped example against its delta schema."""
    document = _load(DELTA)
    registry, uri = _registry(document)
    mapping = _load(EXAMPLES / "schema-map.json")
    errors: list[str] = []
    for filename, schema_name in mapping.items():
        path = EXAMPLES / filename
        if not path.exists():
            errors.append(f"{filename}: missing example")
            continue
        schema = {"$ref": f"{uri}#/components/schemas/{schema_name}"}
        validator = Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())
        problems = sorted(validator.iter_errors(_load(path)), key=lambda item: item.path)
        for problem in problems:
            location = ".".join(str(part) for part in problem.path) or "<root>"
            errors.append(f"{filename} ({schema_name}) {location}: {problem.message}")
    return errors


def validate_delta() -> list[str]:
    """Validate the delta document itself."""
    try:
        validate(_load(DELTA))
    except Exception as exc:
        return [f"android delta: invalid OpenAPI: {exc}"]
    return []


def report_delta_gap() -> list[str]:
    """List delta operations not yet implemented by the current services."""
    delta = _operations(_load(DELTA))
    implemented: set[tuple[str, str]] = set()
    for path in SNAPSHOTS.glob("*.json"):
        implemented |= _operations(_load(path))
    return [f"{method.upper()} {path}" for method, path in sorted(delta - implemented)]


def main() -> int:
    """Run validations and return a non-zero status on failure."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-delta", action="store_true")
    args = parser.parse_args()
    errors = validate_snapshots() + validate_delta() + validate_examples()
    missing = report_delta_gap()
    print(f"delta operations pending: {len(missing)}")
    for item in missing:
        print(f"  pending {item}")
    if args.require_delta and missing:
        errors.extend(f"not implemented: {item}" for item in missing)
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        print(f"{len(errors)} contract error(s)", file=sys.stderr)
        return 1
    print("contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
