"""Opt-in live smoke against running services with synthetic data.

Set SMOKE_EMAIL and SMOKE_PASSWORD for a pre-verified account. Provider
credentials stay outside this script. No token or content is printed.
"""

from __future__ import annotations

import json
import os
import uuid

import httpx

IDENTITY = os.environ.get("SMOKE_IDENTITY", "http://localhost:8001")
CONVERSATION = os.environ.get("SMOKE_CONVERSATION", "http://localhost:8010")
SPEECH = os.environ.get("SMOKE_SPEECH", "http://localhost:8011")


def main() -> int:
    """Login and exercise health, conversation and voice catalog."""
    email = os.environ.get("SMOKE_EMAIL")
    password = os.environ.get("SMOKE_PASSWORD")
    if not email or not password:
        print("SMOKE_EMAIL/SMOKE_PASSWORD not set; live smoke not executed")
        return 0
    with httpx.Client(timeout=30) as client:
        login = client.post(
            f"{IDENTITY}/v1/auth/login",
            json={
                "email": email,
                "password": password,
                "device_id": str(uuid.uuid4()),
                "platform": "android",
            },
        )
        print("login", login.status_code)
        if login.status_code != 200:
            return 1
        tokens = login.json()
        headers = {
            "Authorization": f"Bearer {tokens['access_token']}",
            "X-Session-Source": tokens["source"],
        }
        me = client.get(f"{IDENTITY}/v1/me", headers=headers)
        print("me", me.status_code)
        payload = {
            "client_message_id": str(uuid.uuid4()),
            "conversation_id": "smoke",
            "mode": "conversation",
            "message": "Olá, resposta sintética.",
            "locale": "pt-BR",
            "timezone": "UTC",
            "context": {"records": []},
        }
        with client.stream(
            "POST",
            f"{CONVERSATION}/v1/ai/responses",
            headers={**headers, "Idempotency-Key": f"smoke-{uuid.uuid4()}"},
            json=payload,
        ) as response:
            print("conversation", response.status_code)
            for line in response.iter_lines():
                if line.startswith("event: result"):
                    print("conversation_result", "received")
                    break
        voices = client.get(f"{SPEECH}/v1/speech/voices", headers=headers)
        print("voices", voices.status_code, len(json.dumps(voices.json())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
