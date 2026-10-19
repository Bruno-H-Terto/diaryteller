"""Verify lock files and service dependency declarations."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = [
    ROOT,
    ROOT / "api",
    *sorted((ROOT / "services").glob("*/pyproject.toml")),
]


def main() -> int:
    """Run `poetry check --lock` for the workspace and each service."""
    for project in PROJECTS:
        directory = project if project.is_dir() else project.parent
        result = subprocess.run(
            ["poetry", "check", "--lock"], cwd=directory, capture_output=True, text=True
        )
        status = "ok" if result.returncode == 0 else "failed"
        print(f"{directory.relative_to(ROOT)}: {status}")
        if result.returncode != 0:
            print(result.stdout + result.stderr)
            return 1
    print(f"python {sys.version.split()[0]} satisfies >=3.12,<3.15")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
