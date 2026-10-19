"""Entry point kept next to load-test documentation."""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    """Delegate to the root load script."""
    return subprocess.call([sys.executable, "scripts/load_streams.py", *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
