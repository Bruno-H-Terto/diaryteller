package com.callme.ai.features.conversations.adapters

import com.callme.ai.core.database.DiaryEntity as EntityRow
import com.callme.ai.core.database.DiarySnapshotDao
import com.callme.ai.core.database.EntitiesDao
import com.callme.ai.core.database.EventEntity
import com.callme.ai.core.database.EventEntityLink
import com.callme.ai.core.database.EventRecordLink
import com.callme.ai.core.database.RecordEntityLink
import com.callme.ai.core.database.RelationshipEntity
import com.callme.ai.core.model.DatePrecision
import com.callme.ai.features.conversations.application.DiaryMutator
import com.callme.ai.features.conversations.domain.AppliedChange
import com.callme.ai.features.conversations.domain.AppliedKind
import com.callme.ai.features.conversations.domain.Certainty
import com.callme.ai.features.conversations.domain.DiaryAction
import com.callme.ai.features.conversations.domain.DiarySnapshot
import com.callme.ai.features.conversations.domain.SnapshotEntity
import com.callme.ai.features.conversations.domain.SnapshotEvent
import com.callme.ai.features.entities.domain.EntityType
import java.time.LocalDate
import java.util.UUID

/**
 * Applies a conversation's proposals to the local database.
 *
 * Entities and events created from an explicit statement are confirmed; an
 * inferred one starts as `SUGGESTED` and waits in the review queue, so the chat
 * never silently rewrites what the user said.
 */
class RoomDiaryMutator(
    private val dao: EntitiesDao,
    private val snapshotDao: DiarySnapshotDao,
    private val newId: () -> String = { UUID.randomUUID().toString() },
    private val now: () -> Long = { System.currentTimeMillis() },
    private val today: () -> LocalDate = { LocalDate.now() },
) : DiaryMutator {

    override suspend fun snapshot(): DiarySnapshot = DiarySnapshot(
        entities = snapshotDao.recentEntities(MAX_ENTITIES).map { row ->
            SnapshotEntity(row.id, entityType(row.type), row.name, snapshotDao.relationLabel(row.id).orEmpty())
        },
        events = snapshotDao.recentEvents(MAX_EVENTS).map { row ->
            SnapshotEvent(row.id, row.title, row.eventDate, precision(row.datePrecision))
        },
        today = today().toString(),
    )

    override suspend fun apply(actions: List<DiaryAction>, recordId: String?): List<AppliedChange> {
        val created = mutableMapOf<String, String>()
        val changes = mutableListOf<AppliedChange>()
        for (action in actions) {
            when (action) {
                is DiaryAction.CreateEntity -> {
                    if (action.name.isBlank()) continue
                    created[action.ref] = createEntity(action)
                    changes += AppliedChange(AppliedKind.ENTITY, action.name.trim())
                }
                is DiaryAction.CreateEvent -> {
                    created[action.ref] = createEvent(action, created, recordId)
                    changes += AppliedChange(AppliedKind.EVENT, action.title)
                }
                is DiaryAction.LinkEntity -> {
                    val entityId = created[action.entity] ?: action.entity
                    link(action, entityId, created, recordId)
                    changes += AppliedChange(AppliedKind.LINK, dao.entity(entityId)?.name.orEmpty())
                }
                is DiaryAction.SetEventDate -> {
                    val eventId = created[action.event] ?: action.event
                    dao.setEventDate(eventId, action.date, action.precision.name, now())
                    changes += AppliedChange(AppliedKind.DATE, action.date)
                }
            }
        }
        return changes
    }

    private suspend fun createEntity(action: DiaryAction.CreateEntity): String {
        val id = newId()
        val moment = now()
        val state = state(action.certainty)
        dao.insert(
            EntityRow(
                id = id,
                type = action.type.name,
                name = action.name.trim(),
                avatarModel = model(action.type),
                avatarBackground = BACKGROUND,
                skinColor = null,
                hairColor = null,
                clothingColor = null,
                createdAt = moment,
                updatedAt = moment,
            ),
        )
        if (action.relation.isNotBlank()) {
            dao.upsertRelationship(
                RelationshipEntity(
                    id = newId(),
                    fromEntityId = SELF,
                    toEntityId = id,
                    label = action.relation.trim(),
                    origin = state.origin,
                    reviewState = state.review,
                    sourceRecordId = null,
                    createdAt = moment,
                ),
            )
        }
        return id
    }

    private suspend fun createEvent(
        action: DiaryAction.CreateEvent,
        created: Map<String, String>,
        recordId: String?,
    ): String {
        val id = newId()
        val state = state(action.certainty)
        dao.upsertEvent(
            EventEntity(
                id = id,
                title = action.title,
                summary = action.summary,
                eventDate = action.date,
                datePrecision = action.precision.name,
                coverUri = null,
                origin = state.origin,
                reviewState = state.review,
                updatedAt = now(),
            ),
        )
        (action.sourceIds + listOfNotNull(recordId)).distinct().forEach { source ->
            dao.insertEventRecord(EventRecordLink(id, source))
        }
        action.participants.forEach { reference ->
            val entityId = created[reference] ?: reference
            dao.insertEventEntity(EventEntityLink(id, entityId, role(entityId)))
        }
        return id
    }

    private suspend fun link(
        action: DiaryAction.LinkEntity,
        entityId: String,
        created: Map<String, String>,
        recordId: String?,
    ) {
        val review = state(action.certainty).review
        val source = action.sourceId ?: recordId
        if (source != null && dao.recordExists(source) > 0 && dao.entity(entityId) != null) {
            dao.upsertLink(RecordEntityLink(source, entityId, AI_ORIGIN, review))
        }
        action.event?.let { reference ->
            val eventId = created[reference] ?: reference
            dao.insertEventEntity(EventEntityLink(eventId, entityId, role(entityId)))
        }
    }

    private suspend fun role(entityId: String): String =
        if (dao.entity(entityId)?.type == EntityType.PLACE.name) PLACE else PERSON

    private fun entityType(value: String): EntityType =
        runCatching { EntityType.valueOf(value) }.getOrDefault(EntityType.PERSON)

    private fun precision(value: String): DatePrecision =
        runCatching { DatePrecision.valueOf(value) }.getOrDefault(DatePrecision.UNKNOWN)

    private fun model(type: EntityType): String = when (type) {
        EntityType.ANIMAL -> "a1"
        EntityType.PLACE -> "l1"
        EntityType.EVENT -> "e1"
        else -> "p1"
    }

    /** Review state and origin derived from how certain the model was. */
    private fun state(certainty: Certainty): AppliedState =
        if (certainty == Certainty.EXPLICIT) {
            AppliedState(CONFIRMED, DECLARED)
        } else {
            AppliedState(SUGGESTED, SUGGESTED)
        }

    private companion object {
        const val SELF = "self"
        const val CONFIRMED = "CONFIRMED"
        const val SUGGESTED = "SUGGESTED"
        const val DECLARED = "DECLARED"
        const val AI_ORIGIN = "AI"
        const val PERSON = "PERSON"
        const val PLACE = "PLACE"
        const val BACKGROUND = 0xFFEAE5F6
        const val MAX_ENTITIES = 60
        const val MAX_EVENTS = 40
    }
}

/** The two strings one certainty maps to in the local schema. */
private data class AppliedState(val review: String, val origin: String)
