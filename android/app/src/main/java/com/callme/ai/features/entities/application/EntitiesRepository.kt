package com.callme.ai.features.entities.application

import com.callme.ai.core.model.AvatarStyle
import com.callme.ai.core.model.Period
import com.callme.ai.features.entities.domain.DiaryEntity
import com.callme.ai.features.entities.domain.EntityProfile
import com.callme.ai.features.entities.domain.EntityType
import kotlinx.coroutines.flow.Flow

/**
 * Local registry of the people, animals, places and dates that appear in the
 * diary. Identity is stable: renaming or restyling never detaches mentions.
 */
interface EntitiesRepository {
    fun observeEntities(): Flow<List<DiaryEntity>>
    fun observeProfile(entityId: String, period: Period): Flow<EntityProfile?>
    fun observeSuggestionCount(): Flow<Int>
    suspend fun create(type: EntityType, name: String): String
    suspend fun rename(entityId: String, name: String)
    suspend fun updateAvatar(entityId: String, avatar: AvatarStyle)
    suspend fun setRelationLabel(entityId: String, label: String)
    suspend fun ensureSelf()
}
