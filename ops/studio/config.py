"""Settings for the local studio: bridge address, database and catalogue paths.

Values come from the environment, then from the repository `.env` so the studio
shares the stack configuration. Nothing here is used by the pods.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATIC = Path(__file__).resolve().parent / "static"
CATALOGUES = ROOT / "android" / "i18n"


def read_dotenv() -> dict[str, str]:
    """Parse the repository `.env` without pulling in a dependency."""
    path = ROOT / ".env"
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


@dataclass(frozen=True)
class Settings:
    """Everything the panel needs to reach the app and the stack."""

    bridge_url: str
    database_url: str
    services: list[dict[str, str]]

    @classmethod
    def load(cls) -> Settings:
        """Build settings from the environment, falling back to `.env`."""
        dotenv = read_dotenv()

        def value(name: str, default: str = "") -> str:
            return os.environ.get(name) or dotenv.get(name) or default

        return cls(
            bridge_url=value("DEV_BRIDGE_URL", "http://127.0.0.1:5557"),
            database_url=value("STUDIO_DATABASE_URL") or published(value("DATABASE_URL")),
            services=[
                _service(
                    "api", value("IDENTITY_INTERNAL_URL", "http://localhost:8001"), "/openapi.json"
                ),
                _service("conversation", "http://localhost:8010", "/openapi.json"),
                _service("exchange", "http://localhost:8012", "/openapi.json"),
                _service("dex", "http://localhost:5556", "/dex/.well-known/openid-configuration"),
                _service("mailpit", "http://localhost:8025", "/"),
            ],
        )


def _service(name: str, url: str, probe: str) -> dict[str, str]:
    """Pair a service with the path that proves it is answering."""
    return {"name": name, "url": url, "probe": url.rstrip("/") + probe}


def published(database_url: str) -> str:
    """Point the studio at the port compose publishes, not the container port."""
    if not database_url:
        return ""
    return database_url.replace("@localhost:5432/", "@localhost:55432/").replace(
        "@127.0.0.1:5432/",
        "@127.0.0.1:55432/",
    )
