"""Context and deletion persistence aliases."""

from __future__ import annotations

from ..context_repository import PostgresContextRepository
from ..deletion_repository import PostgresDeletionRepository

ContextRepository = PostgresContextRepository
DeletionRepository = PostgresDeletionRepository
