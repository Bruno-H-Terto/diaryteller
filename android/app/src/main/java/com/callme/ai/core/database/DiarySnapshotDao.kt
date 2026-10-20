package com.callme.ai.core.database

import androidx.room.Dao
import androidx.room.Query

/** Read-only queries that build the compact state sent with a conversation turn. */
@Dao
interface DiarySnapshotDao {

    @Query("SELECT * FROM diary_entities WHERE type != 'SELF' ORDER BY updatedAt DESC LIMIT :limit")
    suspend fun recentEntities(limit: Int): List<DiaryEntity>

    @Query(
        """
        SELECT * FROM events
        ORDER BY COALESCE(eventDate, '') DESC, updatedAt DESC
        LIMIT :limit
        """,
    )
    suspend fun recentEvents(limit: Int): List<EventEntity>

    @Query(
        """
        SELECT label FROM relationships
        WHERE toEntityId = :entityId AND reviewState != 'SUGGESTED'
        LIMIT 1
        """,
    )
    suspend fun relationLabel(entityId: String): String?
}
