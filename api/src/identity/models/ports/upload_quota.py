"""Upload quota persistence aliases."""

from __future__ import annotations

from ..upload_quota_gauge_repository import PostgresUploadQuotaGaugeRepository
from ..upload_quota_repository import PostgresUploadQuotaRepository

UploadQuotaRepository = PostgresUploadQuotaRepository
UploadQuotaGaugeRepository = PostgresUploadQuotaGaugeRepository
