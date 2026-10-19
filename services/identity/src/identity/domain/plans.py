"""Engineering fixtures for upload limits.

These numbers are configurable test fixtures, not commercial prices or approved
product limits. Production must configure them explicitly.
"""

from __future__ import annotations

from diary_contracts.quota import UploadMetric

MIB = 1024 * 1024

FREE_UPLOAD_LIMITS: dict[str, int] = {
    UploadMetric.DAILY_UPLOAD_COUNT.value: 5,
    UploadMetric.DAILY_UPLOAD_BYTES.value: 20 * MIB,
    UploadMetric.RETAINED_STORAGE_BYTES.value: 50 * MIB,
    UploadMetric.CONCURRENT_UPLOADS.value: 2,
    "max_file_bytes": 10 * MIB,
    "max_context_bytes": 20 * MIB,
    "max_context_records": 50,
    "max_audio_seconds": 120,
}

PAID_TEST_UPLOAD_LIMITS: dict[str, int] = {
    UploadMetric.DAILY_UPLOAD_COUNT.value: 100,
    UploadMetric.DAILY_UPLOAD_BYTES.value: 500 * MIB,
    UploadMetric.RETAINED_STORAGE_BYTES.value: 1024 * MIB,
    UploadMetric.CONCURRENT_UPLOADS.value: 4,
    "max_file_bytes": 100 * MIB,
    "max_context_bytes": 50 * MIB,
    "max_context_records": 50,
    "max_audio_seconds": 300,
}


def upload_limits_for(plan_code: str) -> dict[str, int]:
    """Return fixture limits for a plan; unknown plans fall back to free."""
    if plan_code in {"plus", "pro", "paid_test"}:
        return dict(PAID_TEST_UPLOAD_LIMITS)
    return dict(FREE_UPLOAD_LIMITS)
