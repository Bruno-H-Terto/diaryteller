"""Entry point: `poetry run python -m ops.studio` serves the panel on loopback."""

from __future__ import annotations

import uvicorn

from .config import Settings


def main() -> None:
    """Run the studio on the loopback interface only."""
    settings = Settings.load()
    print(f"studio on http://127.0.0.1:8099  (app bridge: {settings.bridge_url})")
    uvicorn.run("ops.studio.server:app", host="127.0.0.1", port=8099, log_level="warning")


if __name__ == "__main__":
    main()
