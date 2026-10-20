package com.callme.ai.core.database

import androidx.room.Dao
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

/** One entity with its frequency inside the selected period. */
data class ConnectionRow(
    val id: String,
    val type: String,
    val name: String,
    val avatarModel: String,
    val avatarBackground: Long,
    val skinColor: Long?,
    val hairColor: Long?,
    val clothingColor: Long?,
    val recordCount: Int,
    val label: String,
    val origin: String,
)

/** Event header used by the timeline and detail screens. */
data class EventRow(
    val id: String,
    val title: String,
    val summary: String,
    val eventDate: String?,
    val datePrecision: String,
    val coverUri: String?,
    val origin: String,
    val reviewState: String,
    val updatedAt: Long,
    val sourceCount: Int,
)

data class EventEntityRow(
    val eventId: String,
    val entityId: String,
    val type: String,
    val name: String,
    val avatarModel: String,
    val avatarBackground: Long,
    val skinColor: Long?,
    val hairColor: Long?,
    val clothingColor: Long?,
    val role: String,
)

data class EventSourceRow(
    val eventId: String,
    val recordId: String,
    val preview: String,
    val diaryDate: String?,
    val recordingId: String?,
    val createdAt: Long,
)

data class ReviewRow(
    val kind: String,
    val id: String,
    val title: String,
    val subtitle: String,
    val dateValue: String,
    val datePrecision: String,
)

@Dao
interface ConnectionsDao {

    @Query(
        """
        SELECT e.id, e.type, e.name, e.avatarModel, e.avatarBackground,
               e.skinColor, e.hairColor, e.clothingColor,
               COUNT(DISTINCT l.recordId) AS recordCount,
               COALESCE(r.label, '') AS label,
               COALESCE(r.origin, 'CONFIRMED') AS origin
        FROM diary_entities e
        JOIN record_entity_links l ON l.entityId = e.id AND l.reviewState = 'CONFIRMED'
        JOIN record_metadata m ON m.recordId = l.recordId
        LEFT JOIN relationships r ON r.toEntityId = e.id AND r.fromEntityId = 'self'
        WHERE m.diaryDate BETWEEN :start AND :end
          AND e.type != 'SELF'
          AND (:type IS NULL OR e.type = :type)
          AND (:query = '' OR e.name LIKE '%' || :query || '%')
        GROUP BY e.id
        ORDER BY recordCount DESC, e.name COLLATE NOCASE
        LIMIT :limit
        """,
    )
    fun connectionsFlow(
        start: String,
        end: String,
        type: String?,
        query: String,
        limit: Int,
    ): Flow<List<ConnectionRow>>

    @Query(
        """
        SELECT COUNT(DISTINCT e.id)
        FROM diary_entities e
        JOIN record_entity_links l ON l.entityId = e.id AND l.reviewState = 'CONFIRMED'
        JOIN record_metadata m ON m.recordId = l.recordId
        WHERE m.diaryDate BETWEEN :start AND :end
          AND e.type != 'SELF'
          AND (:type IS NULL OR e.type = :type)
          AND (:query = '' OR e.name LIKE '%' || :query || '%')
        """,
    )
    fun connectionTotal(start: String, end: String, type: String?, query: String): Flow<Int>

    @Query("SELECT COUNT(*) FROM record_metadata WHERE diaryDate BETWEEN :start AND :end")
    fun recordsInPeriod(start: String, end: String): Flow<Int>

    @Query(
        """
        SELECT COUNT(*) FROM record_metadata
        WHERE diaryDate BETWEEN :start AND :end AND recordingId IS NOT NULL
        """,
    )
    fun audioInPeriod(start: String, end: String): Flow<Int>

    @Query(
        """
        SELECT ev.id, ev.title, ev.summary, ev.eventDate, ev.datePrecision, ev.coverUri,
               ev.origin, ev.reviewState, ev.updatedAt,
               (SELECT COUNT(*) FROM event_record_links x WHERE x.eventId = ev.id) AS sourceCount
        FROM events ev
        WHERE ev.reviewState = :state
          AND (ev.eventDate IS NULL OR ev.eventDate BETWEEN :start AND :end)
        ORDER BY (ev.eventDate IS NULL), ev.eventDate DESC, ev.updatedAt DESC
        LIMIT :limit OFFSET :offset
        """,
    )
    fun events(state: String, start: String, end: String, limit: Int, offset: Int): Flow<List<EventRow>>

    @Query(
        """
        SELECT ev.id, ev.title, ev.summary, ev.eventDate, ev.datePrecision, ev.coverUri,
               ev.origin, ev.reviewState, ev.updatedAt,
               (SELECT COUNT(*) FROM event_record_links x WHERE x.eventId = ev.id) AS sourceCount
        FROM events ev WHERE ev.id = :eventId
        """,
    )
    fun observeEventRow(eventId: String): Flow<EventRow?>

    @Query("SELECT * FROM events WHERE id = :eventId")
    fun event(eventId: String): EventEntity?

    @Query("SELECT * FROM events WHERE title = :title AND eventDate IS :date LIMIT 1")
    fun matchingEvent(title: String, date: String?): EventEntity?

    @Query(
        """
        SELECT el.eventId, e.id AS entityId, e.type, e.name, e.avatarModel, e.avatarBackground,
               e.skinColor, e.hairColor, e.clothingColor, el.role
        FROM event_entity_links el
        JOIN diary_entities e ON e.id = el.entityId
        WHERE el.eventId IN (:eventIds)
        """,
    )
    fun eventEntities(eventIds: List<String>): Flow<List<EventEntityRow>>

    @Query(
        """
        SELECT erl.eventId, r.id AS recordId, r.preview, m.diaryDate, m.recordingId, r.createdAt
        FROM event_record_links erl
        JOIN records r ON r.id = erl.recordId
        LEFT JOIN record_metadata m ON m.recordId = r.id
        WHERE erl.eventId IN (:eventIds)
        ORDER BY m.diaryDate, r.createdAt
        """,
    )
    fun eventSources(eventIds: List<String>): Flow<List<EventSourceRow>>

    @Query(
        """
        SELECT 'LINK' AS kind, l.recordId || '|' || l.entityId AS id, e.name AS title,
               r.preview AS subtitle, '' AS dateValue, '' AS datePrecision
        FROM record_entity_links l
        JOIN diary_entities e ON e.id = l.entityId
        JOIN records r ON r.id = l.recordId
        WHERE l.reviewState = 'SUGGESTED'
        UNION ALL
        SELECT 'RELATION', rel.id, e.name, rel.label, '', ''
        FROM relationships rel
        JOIN diary_entities e ON e.id = rel.toEntityId
        WHERE rel.reviewState = 'SUGGESTED'
        UNION ALL
        SELECT 'EVENT', ev.id, ev.title, ev.summary,
               COALESCE(ev.eventDate, ''), ev.datePrecision
        FROM events ev
        WHERE ev.reviewState = 'SUGGESTED'
        """,
    )
    fun reviewItems(): Flow<List<ReviewRow>>
}
