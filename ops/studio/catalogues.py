"""Summarizes the translation catalogues so the panel can show language coverage.

The studio reads `android/i18n/*.yml` with the same rules as the generator: the
file with the most keys is the reference and missing keys in other languages are
reported as pending translations.
"""

from __future__ import annotations

from pathlib import Path

import yaml


def summary(directory: Path) -> dict:
    """Return language labels, key counts and the keys still missing."""
    catalogues: dict[str, dict] = {}
    for path in sorted(directory.glob("*.yml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        catalogues[path.stem] = {
            "file": path.name,
            "language": data.get("language", path.stem),
            "label": data.get("label", path.stem),
            "strings": data.get("strings") or {},
            "plurals": data.get("plurals") or {},
        }
    if not catalogues:
        return {"languages": [], "reference": None}
    reference = max(catalogues, key=lambda name: len(catalogues[name]["strings"]))
    reference_keys = set(catalogues[reference]["strings"])
    languages = [
        {
            "file": data["file"],
            "language": data["language"],
            "label": data["label"],
            "strings": len(data["strings"]),
            "plurals": len(data["plurals"]),
            "missing": sorted(reference_keys - set(data["strings"])),
        }
        for name, data in catalogues.items()
    ]
    return {"languages": languages, "reference": catalogues[reference]["language"]}
