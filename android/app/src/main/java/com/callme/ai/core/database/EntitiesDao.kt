package com.callme.ai.core.database

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface EntitiesDao {

    @Query("SELECT * FROM diary_entities WHERE type != 'SELF' ORDER BY type, name COLLATE NOCASE")
    fun observeEntities(): Flow<List<DiaryEntity>>

    @Query("SELECT * FROM diary_entities WHERE id = :id")
    fun observeEntity(id: String): Flow<DiaryEntity?>

    @Query("SELECT * FROM diary_entities WHERE id = :id")
    suspend fun entity(id: String): DiaryEntity?

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insert(entity: DiaryEntity)

    @Query(
        """
        UPDATE diary_entities
        SET name = :name, avatarModel = :model, avatarBackground = :background,
            skinColor = :skin, hairColor = :hair, clothingColor = :clothing, updatedAt = :now
        WHERE id = :id
        """,
    )
    suspend fun updateIdentity(
        id: String,
        name: String,
        model: String,
        background: Long,
        skin: Long?,
        hair: Long?,
        clothing: Long?,
        now: Long,
    )

    @Query("SELECT COUNT(*) FROM record_entity_links WHERE entityId = :id")
    suspend fun linkCount(id: String): Int

    @Query("SELECT * FROM relationships WHERE fromEntityId = 'self' AND toEntityId = :entityId LIMIT 1")
    fun observeRelationship(entityId: String): Flow<RelationshipEntity?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertRelationship(relationship: RelationshipEntity)

    @Query("UPDATE relationships SET reviewState = :state WHERE id = :id")
    suspend fun setRelationshipReview(id: String, state: String)

    @Query("DELETE FROM relationships WHERE id = :id")
    suspend fun deleteRelationship(id: String)

    @Query("SELECT * FROM record_entity_links WHERE recordId = :recordId AND entityId = :entityId")
    suspend fun link(recordId: String, entityId: String): RecordEntityLink?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertLink(link: RecordEntityLink)

    @Query(
        """
        UPDATE record_entity_links SET reviewState = :state
        WHERE recordId = :recordId AND entityId = :entityId
        """,
    )
    suspend fun setLinkReview(recordId: String, entityId: String, state: String)

    @Query("DELETE FROM record_entity_links WHERE recordId = :recordId AND entityId = :entityId")
    suspend fun deleteLink(recordId: String, entityId: String)

    @Query(
        """
        SELECT COUNT(DISTINCT l.recordId) FROM record_entity_links l
        JOIN record_metadata m ON m.recordId = l.recordId
        WHERE l.entityId = :entityId AND l.reviewState = 'CONFIRMED'
          AND m.diaryDate BETWEEN :start AND :end
        """,
    )
    fun periodCount(entityId: String, start: String, end: String): Flow<Int>

    @Query(
        """
        SELECT COUNT(DISTINCT l.recordId) FROM record_entity_links l
        WHERE l.entityId = :entityId AND l.reviewState = 'CONFIRMED'
        """,
    )
    fun totalCount(entityId: String): Flow<Int>

    @Query(
        """
        SELECT ev.id, ev.title, ev.summary, ev.eventDate, ev.datePrecision, ev.coverUri,
               ev.origin, ev.reviewState, ev.updatedAt,
               (SELECT COUNT(*) FROM event_record_links x WHERE x.eventId = ev.id) AS sourceCount
        FROM events ev
        JOIN event_entity_links el ON el.eventId = ev.id
        WHERE el.entityId = :entityId AND ev.reviewState = 'CONFIRMED'
        ORDER BY (ev.eventDate IS NULL), ev.eventDate DESC
        LIMIT 12
        """,
    )
    fun eventsOfEntity(entityId: String): Flow<List<EventRow>>

    @Query(
        """
        SELECT r.id, r.createdAt, m.diaryDate, m.recordingId, r.preview
        FROM records r
        JOIN record_entity_links l ON l.recordId = r.id AND l.reviewState = 'CONFIRMED'
        LEFT JOIN record_metadata m ON m.recordId = r.id
        WHERE l.entityId = :entityId
        ORDER BY m.diaryDate DESC, r.createdAt DESC
        LIMIT 20
        """,
    )
    fun recordsOfEntity(entityId: String): Flow<List<EntitySourceRow>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertEvent(event: EventEntity)

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertEventRecord(link: EventRecordLink)

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertEventEntity(link: EventEntityLink)

    @Query("UPDATE events SET reviewState = :state, updatedAt = :now WHERE id = :id")
    suspend fun setEventReview(id: String, state: String, now: Long)

    @Query("UPDATE events SET eventDate = :date, datePrecision = :precision, updatedAt = :now WHERE id = :id")
    suspend fun setEventDate(id: String, date: String?, precision: String, now: Long)

    @Query("DELETE FROM events WHERE id = :id")
    suspend fun deleteEvent(id: String)

    @Query("DELETE FROM event_record_links WHERE eventId = :eventId AND recordId = :recordId")
    suspend fun detachEventSource(eventId: String, recordId: String)

    @Query(
        """
        SELECT COUNT(*) FROM record_entity_links WHERE reviewState = 'SUGGESTED'
        """,
    )
    fun suggestedLinkCount(): Flow<Int>

    @Query("SELECT COUNT(*) FROM events WHERE reviewState = 'SUGGESTED'")
    fun suggestedEventCount(): Flow<Int>

    @Query("SELECT COUNT(*) FROM records WHERE id = :recordId")
    suspend fun recordExists(recordId: String): Int

    @Query("DELETE FROM diary_entities WHERE id LIKE 'sample-%'")
    suspend fun deleteSampleEntities()

    @Query("DELETE FROM events WHERE id LIKE 'sample-%'")
    suspend fun deleteSampleEvents()
}

data class EntitySourceRow(
    val id: String,
    val createdAt: Long,
    val diaryDate: String?,
    val recordingId: String?,
    val preview: String,
)
