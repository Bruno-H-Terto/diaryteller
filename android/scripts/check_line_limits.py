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


def files() -> list[Path]:
    found: list[Path] = []
    for base in INCLUDE:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file() and path.suffix in SUFFIXES:
                if not IGNORED.intersection(path.relative_to(ROOT).parts):
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
