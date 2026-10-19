"""Helpers shared by identity integration tests."""

from __future__ import annotations

import httpx
from sqlalchemy.ext.asyncio import create_async_engine


async def verify_email(email: str, database: str) -> None:
    """Mark an account verified without inspecting the email token."""
    engine = create_async_engine(database)
    try:
        async with engine.begin() as connection:
            from sqlalchemy import text

            await connection.execute(
                text("UPDATE users SET email_verified_at = now() WHERE email = :email"),
                {"email": email},
            )
    finally:
        await engine.dispose()


async def register_and_login(
    client: httpx.AsyncClient, database: str, email: str, device: str
) -> dict:
    register = await client.post(
        "/v1/auth/register",
        json={
            "email": email,
            "password": "correct horse battery",
            "locale": "pt-BR",
            "timezone": "UTC",
        },
    )
    assert register.status_code == 201, register.text
    await verify_email(email, database)
    login = await client.post(
        "/v1/auth/login",
        json={
            "email": email,
            "password": "correct horse battery",
            "device_id": device,
            "platform": "android",
        },
    )
    assert login.status_code == 200, login.text
    return login.json()
