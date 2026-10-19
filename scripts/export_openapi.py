"""Export the real OpenAPI document of every HTTP service.

The script generates throwaway RS256 keys and safe local settings when the
environment is incomplete. Snapshots are generated artifacts: never edit them by
hand. `--baseline` refreshes the compatibility baseline used by CI.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "contracts" / "openapi"
BASELINE = OUTPUT / "baseline"
SERVICES = ("identity", "conversation", "speech", "memory_mcp", "exchange")

_FIXED = {
    "APP_ENV": "test",
    "JWT_ACTIVE_KID": "export-1",
    "JWT_ISSUER": "diary-api",
    "JWT_AUDIENCE": "diary-mobile",
    "SOURCE_ENCRYPTION_KEY": base64.urlsafe_b64encode(b"e" * 32).decode(),
    "MCP_CONTEXT_KEY": base64.urlsafe_b64encode(b"e" * 32).decode(),
    "EMAIL_TOKEN_KEY": base64.urlsafe_b64encode(b"e" * 32).decode(),
    "PUSH_TOKEN_KEY": base64.urlsafe_b64encode(b"e" * 32).decode(),
    "BILLING_TOKEN_KEY": base64.urlsafe_b64encode(b"e" * 32).decode(),
    "IDEMPOTENCY_HMAC_KEY": base64.urlsafe_b64encode(b"e" * 32).decode(),
    "BACKUP_ENCRYPTION_KEY": base64.urlsafe_b64encode(b"e" * 32).decode(),
    "CONVERSATION_INTERNAL_TOKEN": "export-conversation",
    "SPEECH_INTERNAL_TOKEN": "export-speech",
    "IDENTITY_INTERNAL_SECRETS": (
        '{"conversation":"export-conversation","speech":"export-speech"}'
    ),
    "MCP_SERVICE_TOKEN": "export-mcp",
    "BILLING_PROVIDER": "fake",
    "LLM_PROVIDER": "fake",
    "SPEECH_PROVIDER": "fake",
    "PUSH_PROVIDER": "dev",
    "EXCHANGE_DATABASE_URL": "postgresql+asyncpg://diary:diary@localhost:5432/exchange",
    "EXCHANGE_CONTEXT_ENCRYPTION_KEY": base64.urlsafe_b64encode(b"e" * 32).decode(),
    "EXCHANGE_IDENTITY_INTERNAL_TOKEN": "export-exchange",
    "EXCHANGE_INTERNAL_SECRETS": (
        '{"conversation":"export-conversation","speech":"export-speech"}'
    ),
}


def _ensure_keys() -> Path:
    directory = Path(os.environ.get("JWT_KEYS_DIR", tempfile.mkdtemp(prefix="diary-openapi-")))
    directory.mkdir(parents=True, exist_ok=True)
    private = directory / "export-1.private.pem"
    public = directory / "export-1.public.pem"
    if not private.exists():
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        private.write_bytes(
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
        public.write_bytes(
            key.public_key().public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )
    os.environ["JWT_KEYS_DIR"] = str(directory)
    return directory


def _apply_defaults() -> None:
    for key, value in _FIXED.items():
        os.environ.setdefault(key, value)


def export_specs(services: tuple[str, ...] = SERVICES) -> dict[str, dict]:
    """Return `{service: openapi}` without starting lifespans or databases."""
    _apply_defaults()
    _ensure_keys()
    documents: dict[str, dict] = {}
    for service in services:
        module = importlib.import_module(f"{service}.app")
        app = module.create_app()
        documents[service] = app.openapi()
    return documents


def write(documents: dict[str, dict], target: Path) -> list[Path]:
    """Write deterministic JSON snapshots and return their paths."""
    target.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for service, document in sorted(documents.items()):
        path = target / f"{service}.json"
        path.write_text(
            json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        written.append(path)
    return written


def refresh_baseline(services: tuple[str, ...] = SERVICES) -> list[Path]:
    """Replace the committed baseline and record content hashes."""
    documents = export_specs(services)
    if BASELINE.exists():
        shutil.rmtree(BASELINE)
    paths = write(documents, BASELINE)
    manifest = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    (BASELINE / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return paths


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", action="store_true")
    args = parser.parse_args()
    paths = refresh_baseline() if args.baseline else write(export_specs(), OUTPUT)
    for path in paths:
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
