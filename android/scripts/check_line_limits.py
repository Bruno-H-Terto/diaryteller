#!/usr/bin/env python3
"""Fail when a hand-written Android source or test file exceeds 200 lines."""

from __future__ import annotations

import sys
from pathlib import Path

MAX_LINES = 200
ROOT = Path(__file__).resolve().parents[1]
INCLUDE = (ROOT / "app" / "src", ROOT / "scripts")
SUFFIXES = {".kt", ".kts", ".xml", ".py"}
IGNORED = {"build", ".gradle", "__pycache__"}


def generated(path: Path) -> bool:
    """Generated resources come from `android/i18n` and are exempt by design."""
    head = path.read_text(encoding="utf-8", errors="replace")[:200]
    return "GENERATED FILE" in head


def files() -> list[Path]:
    found: list[Path] = []
    for base in INCLUDE:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            relative = path.relative_to(ROOT)
            if (
                path.is_file()
                and path.suffix in SUFFIXES
                and not IGNORED.intersection(relative.parts)
                and not generated(path)
            ):
                found.append(path)
    return found


def main() -> int:
    violations = []
    for path in files():
        lines = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
        if lines > MAX_LINES:
            violations.append((path.relative_to(ROOT), lines))
    for path, lines in violations:
        print(f"{path}: {lines} lines (max {MAX_LINES})", file=sys.stderr)
    if violations:
        return 1
    print(f"android line limit ok ({len(files())} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
