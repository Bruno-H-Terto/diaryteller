"""Create development-only signing keys and local secrets.

The script is idempotent: existing keys and non-placeholder secrets are kept. It
writes `keys/jwt/{kid}.private.pem` and `.public.pem` and fills placeholder
values in `.env`. Nothing generated here belongs in version control.
"""

from __future__ import annotations

import base64
import os
import re
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

ROOT = Path(__file__).resolve().parents[1]
SECRET_KEYS = (
    "SOURCE_ENCRYPTION_KEY",
    "MCP_CONTEXT_KEY",
    "EMAIL_TOKEN_KEY",
    "BACKUP_ENCRYPTION_KEY",
)


def load_env() -> dict[str, str]:
    """Parse the local .env file without importing application settings."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return {}
    values: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def ensure_jwt_keys(kid: str) -> Path:
    """Generate one RSA key pair when the private key is absent."""
    keys_dir = ROOT / os.environ.get("JWT_KEYS_DIR", "keys/jwt")
    keys_dir.mkdir(parents=True, exist_ok=True)
    private_path = keys_dir / f"{kid}.private.pem"
    public_path = keys_dir / f"{kid}.public.pem"
    if private_path.exists():
        return private_path
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    private_path.chmod(0o600)
    public_path.write_bytes(
        key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    return private_path


def update_env(secret: str) -> bool:
    """Replace one placeholder in .env, preserving unrelated lines."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return False
    lines = env_path.read_text(encoding="utf-8").splitlines()
    changed = False
    pattern = re.compile(rf"^{re.escape(secret)}=(.*)$")
    value = base64.urlsafe_b64encode(os.urandom(32)).decode()
    output = []
    for line in lines:
        match = pattern.match(line)
        if match and match.group(1) in {"", "REPLACE_ME"}:
            line = f"{secret}={value}"
            changed = True
        output.append(line)
    env_path.write_text("\n".join(output) + "\n", encoding="utf-8")
    return changed


def main() -> None:
    """Create keys/secrets and print a short, non-secret summary."""
    env = load_env()
    kid = env.get("JWT_ACTIVE_KID", "dev-1")
    path = ensure_jwt_keys(kid)
    print(f"JWT key ready: {path.relative_to(ROOT)}")
    updated = [name for name in SECRET_KEYS if update_env(name)]
    if updated:
        print(f"filled local secrets in .env: {', '.join(updated)}")
    elif not (ROOT / ".env").exists():
        print("copy .env.example to .env before running services")
    else:
        print("local secrets already configured")


if __name__ == "__main__":
    main()
