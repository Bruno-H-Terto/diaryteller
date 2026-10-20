package com.callme.ai.features.entities.adapters

import com.callme.ai.core.database.DiaryEntity as EntityRow
import com.callme.ai.core.database.EventRow
import com.callme.ai.core.database.RelationshipEntity
import com.callme.ai.core.model.AvatarStyle
import com.callme.ai.core.model.DatePrecision
import com.callme.ai.core.model.eventDateLabel
import com.callme.ai.features.entities.domain.DiaryEntity
import com.callme.ai.features.entities.domain.EntityRelation
import com.callme.ai.features.entities.domain.EntitySource
import com.callme.ai.features.entities.domain.EntityType
import com.callme.ai.features.entities.domain.RelatedEvent
import com.callme.ai.features.entities.domain.RelationOrigin
import java.time.LocalDate

internal fun EntityRow.toDomain() = DiaryEntity(
        id = id,
        type = runCatching { EntityType.valueOf(type) }.getOrDefault(EntityType.PERSON),
        name = name,
        avatar = AvatarStyle(
            avatarModel,
            avatarBackground,
            skinColor,
            hairColor,
            clothingColor,
        ),
        updatedAt = updatedAt,
    )

internal fun RelationshipEntity.toRelation() = EntityRelation(
        id = id,
        label = label,
        origin = runCatching { RelationOrigin.valueOf(origin) }.getOrDefault(RelationOrigin.DECLARED),
    )

internal fun EventRow.toRelatedEvent() = RelatedEvent(
        id = id,
        title = title,
        dateLabel = eventDateLabel(
            eventDate?.let { runCatching { LocalDate.parse(it.take(10)) }.getOrNull() },
            runCatching { DatePrecision.valueOf(datePrecision) }.getOrDefault(DatePrecision.UNKNOWN),
        ),
    )

internal fun com.callme.ai.core.database.EntitySourceRow.toSource() = EntitySource(
        recordId = id,
        label = preview.lineSequence().firstOrNull().orEmpty().ifBlank { "Registro" },
        hasAudio = recordingId != null,
    )

    internal fun defaultModel(type: EntityType) = when (type) {
        EntityType.ANIMAL -> "a1"
        EntityType.PLACE -> "l1"
        EntityType.EVENT -> "e1"
        EntityType.PERSON, EntityType.SELF -> "p1"
    }

