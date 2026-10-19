"""Structured proposals the phone may accept, edit and store locally.

A proposal is never an executed action. Every variant requires explicit user
confirmation and carries the local record IDs it was derived from.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProposalType(StrEnum):
    """Discriminator values for local proposals."""

    GOAL = "goal"
    REMINDER = "reminder"
    LOCAL_SUMMARY = "local_summary"


class ProposalBase(BaseModel):
    """Fields shared by all proposals."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    text: str = Field(min_length=1, max_length=1000)
    source_ids: list[str] = Field(default_factory=list, max_length=50)
    requires_confirmation: Literal[True] = True


class GoalProposal(ProposalBase):
    """A possible goal the user can save locally."""

    type: Literal[ProposalType.GOAL] = ProposalType.GOAL


class ReminderProposal(ProposalBase):
    """A proposed reminder; scheduling remains local and user-driven."""

    type: Literal[ProposalType.REMINDER] = ProposalType.REMINDER
    timezone: str = Field(min_length=1, max_length=64)
    proposed_at: datetime | None = None
    needs_clarification: bool = False


class LocalSummaryProposal(ProposalBase):
    """A summary the user may keep in the local diary."""

    type: Literal[ProposalType.LOCAL_SUMMARY] = ProposalType.LOCAL_SUMMARY
    period_start: date | None = None
    period_end: date | None = None


Proposal = Annotated[
    GoalProposal | ReminderProposal | LocalSummaryProposal,
    Field(discriminator="type"),
]


class TimelineEntry(BaseModel):
    """One dated or explicitly undated event with its sources."""

    model_config = ConfigDict(extra="forbid")

    event: str = Field(min_length=1, max_length=1000)
    event_date: date | None = None
    recorded_at: datetime | None = None
    source_ids: list[str] = Field(default_factory=list, max_length=50)
    uncertainty: str | None = Field(default=None, max_length=300)
