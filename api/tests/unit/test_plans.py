"""Plan fixtures stay complete and production seeds stay minimal."""

from __future__ import annotations

from diary_contracts.quota import UploadMetric
from identity.config.seed import plans_for
from identity.models.plans import FREE_UPLOAD_LIMITS

REQUIRED_LIMITS = {
    UploadMetric.DAILY_UPLOAD_COUNT.value,
    UploadMetric.DAILY_UPLOAD_BYTES.value,
    UploadMetric.RETAINED_STORAGE_BYTES.value,
    UploadMetric.CONCURRENT_UPLOADS.value,
    "max_file_bytes",
    "max_context_bytes",
    "max_context_records",
    "max_audio_seconds",
}


def test_every_plan_declares_all_upload_limits() -> None:
    for plan in plans_for("test"):
        assert set(plan.upload_limits) >= REQUIRED_LIMITS, plan.code
        assert all(value > 0 for value in plan.upload_limits.values()), plan.code


def test_production_has_free_plan_and_no_test_fixtures() -> None:
    codes = {plan.code for plan in plans_for("production")}
    assert "free" in codes
    assert "paid_test" not in codes
    default = next(plan for plan in plans_for("production") if plan.is_default)
    assert default.code == "free"
    assert default.upload_limits == FREE_UPLOAD_LIMITS
