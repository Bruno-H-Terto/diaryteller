"""Fail when a hand-written file exceeds the 200 physical line budget.

Generated artifacts are allowlisted explicitly and are never split to bypass the
limit. Binary files and repository metadata are ignored.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

MAX_LINES = 200
ALLOWLIST = {
    "poetry.lock",
    "package-lock.json",
    "uv.lock",
    "openapi.json",
}
IGNORED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".pyright",
    "htmlcov",
    "node_modules",
    "dist",
    "backups",
    "migrations",
    "migrate",
    "build",
    ".gradle",
}
CHECKED_SUFFIXES = {
    ".py",
    ".md",
    ".toml",
    ".yaml",
    ".yml",
    ".sql",
    ".ini",
    ".conf",
    ".sh",
    ".txt",
    ".env",
}
CHECKED_NAMES = {"Makefile", "Dockerfile", "AGENTS.md"}


def iter_files(root: Path) -> list[Path]:
    """Return candidate text files in deterministic order."""
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in IGNORED_DIRS for part in relative.parts):
            continue
        if path.name in ALLOWLIST:
            continue
        if relative.parts[:2] in {("contracts", "openapi"), ("contracts", "android-delta")}:
            continue
        if path.suffix in CHECKED_SUFFIXES or path.name in CHECKED_NAMES:
            files.append(path)
    return files


def count_lines(path: Path) -> int:
    """Count physical lines, treating a missing trailing newline as a line."""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text.count("\n") + (0 if text.endswith("\n") or not text else 1)


def main() -> int:
    """Print violations and return a non-zero status when any file is too long."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="repository root")
    parser.add_argument("--max", type=int, default=MAX_LINES)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    violations = []
    for path in iter_files(root):
        lines = count_lines(path)
        if lines > args.max:
            violations.append((path.relative_to(root), lines))
    for relative, lines in violations:
        print(f"{relative}: {lines} lines (max {args.max})", file=sys.stderr)
    if violations:
        print(f"{len(violations)} file(s) exceed the line limit", file=sys.stderr)
        return 1
    print(f"line limit ok ({len(iter_files(root))} files checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
