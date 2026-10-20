package com.callme.ai.features.entities.domain

import com.callme.ai.core.model.AvatarStyle

/** Kinds of things the diary can mention. `SELF` is the diary owner. */
enum class EntityType { PERSON, ANIMAL, PLACE, EVENT, SELF }

/** Where a relation or mention came from. Only CONFIRMED is presented as fact. */
enum class RelationOrigin { CONFIRMED, DECLARED, SUGGESTED }

data class DiaryEntity(
    val id: String,
    val type: EntityType,
    val name: String,
    val avatar: AvatarStyle,
    val updatedAt: Long,
)

data class EntityRelation(
    val id: String,
    val label: String,
    val origin: RelationOrigin,
)

/** Everything the entity screen shows, assembled from counts and links. */
data class EntityProfile(
    val entity: DiaryEntity,
    val relation: EntityRelation?,
    val periodCount: Int,
    val totalCount: Int,
    val events: List<RelatedEvent>,
    val sources: List<EntitySource>,
)

data class RelatedEvent(val id: String, val title: String, val dateLabel: String)

data class EntitySource(val recordId: String, val label: String, val hasAudio: Boolean)
