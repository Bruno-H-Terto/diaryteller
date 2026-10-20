package com.callme.ai.features.conversations.domain

import com.callme.ai.core.model.DatePrecision
import com.callme.ai.features.entities.domain.EntityType

/**
 * One change the assistant proposed for the local diary.
 *
 * The server never writes diary content: it returns `DiaryAction`s and this app
 * validates and stores them. A reference is either a local id the app sent in
 * the snapshot or a `new:N` ref declared in the same reply, so an action can
 * never point at something that does not exist.
 */
sealed interface DiaryAction {
    val certainty: Certainty

    data class CreateEntity(
        val ref: String,
        val type: EntityType,
        val name: String,
        val relation: String,
        override val certainty: Certainty,
    ) : DiaryAction

    data class CreateEvent(
        val ref: String,
        val title: String,
        val summary: String,
        val date: String?,
        val precision: DatePrecision,
        val participants: List<String>,
        val sourceIds: List<String>,
        override val certainty: Certainty,
    ) : DiaryAction

    data class LinkEntity(
        val entity: String,
        val sourceId: String?,
        val event: String?,
        override val certainty: Certainty,
    ) : DiaryAction

    data class SetEventDate(
        val event: String,
        val date: String,
        val precision: DatePrecision,
        override val certainty: Certainty,
    ) : DiaryAction
}

/** How a fact reached the assistant; maps to `CONFIRMED` or `SUGGESTED`. */
enum class Certainty { EXPLICIT, INFERRED }

/** Entity and event ids the app shares so the assistant can reuse them. */
data class DiarySnapshot(
    val entities: List<SnapshotEntity>,
    val events: List<SnapshotEvent>,
    val today: String,
)

data class SnapshotEntity(val id: String, val type: EntityType, val name: String, val relation: String)

data class SnapshotEvent(val id: String, val title: String, val date: String?, val precision: DatePrecision)

/** What the diary changed after applying a reply, shown as a chip in the chat. */
data class AppliedChange(val kind: AppliedKind, val label: String)

enum class AppliedKind { ENTITY, EVENT, LINK, DATE }
