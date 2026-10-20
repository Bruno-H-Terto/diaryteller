package com.callme.ai.features.entities.adapters

import com.callme.ai.core.database.DiaryEntity as EntityRow
import com.callme.ai.core.database.EntitiesDao
import com.callme.ai.core.database.EventRow
import com.callme.ai.core.database.RelationshipEntity
import com.callme.ai.core.model.AvatarStyle
import com.callme.ai.core.model.Period
import com.callme.ai.core.model.DatePrecision
import com.callme.ai.core.model.eventDateLabel
import com.callme.ai.features.entities.application.EntitiesRepository
import com.callme.ai.features.entities.domain.DiaryEntity
import com.callme.ai.features.entities.domain.EntityProfile
import com.callme.ai.features.entities.domain.EntityRelation
import com.callme.ai.features.entities.domain.EntitySource
import com.callme.ai.features.entities.domain.EntityType
import com.callme.ai.features.entities.domain.RelatedEvent
import com.callme.ai.features.entities.domain.RelationOrigin
import java.time.LocalDate
import java.util.UUID
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.map

/** Keeps the local entity registry and its relationship labels in Room. */
class RoomEntitiesRepository(
    private val dao: EntitiesDao,
    private val newId: () -> String = { UUID.randomUUID().toString() },
    private val now: () -> Long = { System.currentTimeMillis() },
) : EntitiesRepository {

    override fun observeEntities(): Flow<List<DiaryEntity>> =
        dao.observeEntities().map { rows -> rows.map { it.toDomain() } }

    override fun observeSuggestionCount(): Flow<Int> =
        combine(dao.suggestedLinkCount(), dao.suggestedEventCount()) { links, events -> links + events }

    override fun observeProfile(entityId: String, period: Period): Flow<EntityProfile?> {
        val base = combine(
            dao.observeEntity(entityId),
            dao.observeRelationship(entityId),
            dao.periodCount(entityId, period.queryStart.toString(), period.queryEnd.toString()),
            dao.totalCount(entityId),
        ) { entity, relation, periodCount, total ->
            ProfileBase(entity, relation, periodCount, total)
        }
        return base.combine(dao.eventsOfEntity(entityId)) { value, events ->
            value to events
        }.combine(dao.recordsOfEntity(entityId)) { (value, events), sources ->
            val entity = value.entity ?: return@combine null
            EntityProfile(
                entity = entity.toDomain(),
                relation = value.relation?.toRelation(),
                periodCount = value.periodCount,
                totalCount = value.totalCount,
                events = events.map { it.toRelatedEvent() },
                sources = sources.map { it.toSource() },
            )
        }
    }

    private data class ProfileBase(
        val entity: EntityRow?,
        val relation: RelationshipEntity?,
        val periodCount: Int,
        val totalCount: Int,
    )

    override suspend fun create(type: EntityType, name: String): String {
        val id = newId()
        val moment = now()
        dao.insert(
            EntityRow(
                id = id,
                type = type.name,
                name = name.trim(),
                avatarModel = defaultModel(type),
                avatarBackground = DEFAULT_BACKGROUND,
                skinColor = null,
                hairColor = null,
                clothingColor = null,
                createdAt = moment,
                updatedAt = moment,
            ),
        )
        return id
    }

    override suspend fun rename(entityId: String, name: String) {
        val current = dao.entity(entityId) ?: return
        val avatar = AvatarStyle(
            current.avatarModel,
            current.avatarBackground,
            current.skinColor,
            current.hairColor,
            current.clothingColor,
        )
        write(entityId, name, avatar)
    }

    override suspend fun updateAvatar(entityId: String, avatar: AvatarStyle) {
        val current = dao.entity(entityId) ?: return
        write(entityId, current.name, avatar)
    }

    override suspend fun setRelationLabel(entityId: String, label: String) {
        val existing = dao.entity(entityId) ?: return
        val relation = RelationshipEntity(
            id = "self-$entityId",
            fromEntityId = SELF,
            toEntityId = entityId,
            label = label.trim(),
            origin = RelationOrigin.DECLARED.name,
            reviewState = "CONFIRMED",
            sourceRecordId = null,
            createdAt = existing.createdAt,
        )
        if (label.isBlank()) {
            dao.deleteRelationship(relation.id)
        } else {
            dao.upsertRelationship(relation)
        }
    }

    override suspend fun ensureSelf() {
        val moment = now()
        dao.insert(
            EntityRow(
                id = SELF,
                type = EntityType.SELF.name,
                name = "Você",
                avatarModel = "p1",
                avatarBackground = DEFAULT_BACKGROUND,
                skinColor = null,
                hairColor = null,
                clothingColor = null,
                createdAt = moment,
                updatedAt = moment,
            ),
        )
    }

    private suspend fun write(entityId: String, name: String, avatar: AvatarStyle) {
        dao.updateIdentity(
            id = entityId,
            name = name.trim(),
            model = avatar.model,
            background = avatar.background,
            skin = avatar.skin,
            hair = avatar.hair,
            clothing = avatar.clothing,
            now = now(),
        )
    }

    private companion object {
        const val SELF = "self"
        const val DEFAULT_BACKGROUND = 0xFFEAE5F6
    }
}
