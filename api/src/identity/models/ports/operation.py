"""Operation persistence aliases."""

from __future__ import annotations

from ..operation_control_repository import PostgresOperationControlRepository
from ..operation_repository import PostgresOperationRepository

OperationRepository = PostgresOperationRepository
OperationControlRepository = PostgresOperationControlRepository
