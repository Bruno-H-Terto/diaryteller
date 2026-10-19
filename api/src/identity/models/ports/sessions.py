"""Session persistence aliases."""

from __future__ import annotations

from ..refresh_repository import PostgresRefreshRepository
from ..session_repository import PostgresSessionRepository

SessionRepository = PostgresSessionRepository
RefreshRepository = PostgresRefreshRepository
