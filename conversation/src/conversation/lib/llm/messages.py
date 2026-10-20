"""Build provider messages from the current operation only."""

from __future__ import annotations

from pathlib import Path

from conversation.lib.ports import LlmMessage
from diary_contracts.conversation import ConversationRequest


def load_system_prompt(prompts_dir: str) -> str:
    """Read the versioned system prompt."""
    path = Path(prompts_dir) / "system_conversation.txt"
    return path.read_text(encoding="utf-8")


def build_messages(system_prompt: str, request: ConversationRequest) -> list[LlmMessage]:
    """Include selected records as untrusted, clearly delimited data."""
    lines = [
        f"Mode: {request.mode.value}",
        f"Locale: {request.locale}",
        f"Timezone: {request.timezone}",
        "Coverage: only the selected records below were provided.",
    ]
    if request.context.records:
        lines.append("<provided_records>")
        for record in request.context.records:
            lines.append(
                f"[{record.id}] recorded_at={record.recorded_at.isoformat()} "
                f"event_at={record.event_at.isoformat() if record.event_at else 'unknown'} "
                f"type={record.source_type.value}\n{record.text}"
            )
        lines.append("</provided_records>")
    diary = request.diary
    if diary.entities or diary.events:
        lines.append("<diary>")
        if diary.today:
            lines.append(f"today={diary.today.isoformat()}")
        for entity in diary.entities:
            relation = f" relation={entity.relation}" if entity.relation else ""
            lines.append(
                f"entity id={entity.id} kind={entity.kind.value} name={entity.name}{relation}"
            )
        for event in diary.events:
            when = event.event_date.isoformat() if event.event_date else "undated"
            lines.append(
                f"event id={event.id} date={when} precision={event.precision.value} "
                f"title={event.title}"
            )
        lines.append("</diary>")
    if diary.draft:
        lines.append("<draft>")
        lines.append(diary.draft)
        lines.append("</draft>")
    lines.append("<user_message>")
    lines.append(request.message)
    lines.append("</user_message>")
    return [
        LlmMessage(role="system", content=system_prompt),
        LlmMessage(role="user", content="\n".join(lines)),
    ]
