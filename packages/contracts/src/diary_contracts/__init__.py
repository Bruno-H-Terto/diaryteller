"""Transport contracts shared by the diary services.

Only JSON-facing schemas live here. Domain entities and ORM models stay inside
their owning service.
"""

from .authorization import (
    AccountStatus,
    AuthorizeDecision,
    AuthorizeRequest,
    EntitlementView,
    Permission,
    UsageMetric,
)
from .context import ContextBundle, ContextRecord, SourceType
from .conversation import FinalResult, ResponseMode
from .errors import DomainError, ErrorCode, ErrorEnvelope
from .operation import (
    OperationState,
    OperationType,
    OperationView,
    ReserveRequest,
    ReserveResult,
)
from .suggestions import Proposal, TimelineEntry

__all__ = [
    "AccountStatus",
    "AuthorizeDecision",
    "AuthorizeRequest",
    "ContextBundle",
    "ContextRecord",
    "DomainError",
    "EntitlementView",
    "ErrorCode",
    "ErrorEnvelope",
    "FinalResult",
    "OperationState",
    "OperationType",
    "OperationView",
    "Permission",
    "Proposal",
    "ReserveRequest",
    "ReserveResult",
    "ResponseMode",
    "SourceType",
    "TimelineEntry",
    "UsageMetric",
]
