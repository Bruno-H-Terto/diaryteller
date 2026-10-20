package com.callme.ai.features.connections.adapters

import com.callme.ai.core.database.ConnectionRow
import com.callme.ai.core.database.ConnectionsDao
import com.callme.ai.core.database.EntitiesDao
import com.callme.ai.core.database.EventEntityRow
import com.callme.ai.core.database.EventRow
import com.callme.ai.core.database.EventSourceRow
import com.callme.ai.core.model.AvatarStyle
import com.callme.ai.core.model.DatePrecision
import com.callme.ai.core.model.eventDateLabel
import com.callme.ai.core.model.Period
import com.callme.ai.features.connections.application.ConnectionsRepository
import com.callme.ai.features.connections.application.MapData
import com.callme.ai.features.connections.domain.ConnectionNode
import com.callme.ai.features.connections.domain.EventSource
import com.callme.ai.features.connections.domain.MapSummary
import com.callme.ai.features.connections.domain.Participant
import com.callme.ai.features.connections.domain.ReviewItem
import com.callme.ai.features.connections.domain.ReviewKind
import com.callme.ai.features.connections.domain.TimelineEvent
import com.callme.ai.features.entities.domain.EntityType
import com.callme.ai.features.entities.domain.RelationOrigin
import java.time.LocalDate
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.map

/** Reads the connections map and timeline straight from Room, without loading texts. */
class RoomConnectionsRepository(
    private val dao: ConnectionsDao,
    private val entities: EntitiesDao,
    private val now: () -> Long = { System.currentTimeMillis() },
) : ConnectionsRepository {

    override fun observeMap(period: Period, type: EntityType?, query: String): Flow<MapData> {
        val start = period.queryStart.toString()
        val end = period.queryEnd.toString()
        val filter = type?.takeIf { it != EntityType.SELF }?.name
        val total = dao.connectionsFlow(start, end, filter, query, LIMIT)
        return combine(
            total,
            dao.connectionTotal(start, end, filter, query),
            dao.recordsInPeriod(start, end),
            dao.audioInPeriod(start, end),
        ) { rows, neighbours, records, audio ->
            MapData(
                nodes = rows.map(::toNode),
                summary = MapSummary(records, audio, neighbours),
            )
        }
    }

    override fun observeTimeline(period: Period, limit: Int): Flow<List<TimelineEvent>> =
        dao.events(CONFIRMED, period.queryStart.toString(), period.queryEnd.toString(), limit, 0)
            .flatMapLatest { rows -> withRelated(rows) }

    override fun observeEvent(eventId: String): Flow<TimelineEvent?> =
        dao.observeEventRow(eventId).flatMapLatest { row ->
            if (row == null) flowOf(null) else withRelated(listOf(row)).map { it.firstOrNull() }
        }

    override suspend fun setEventDate(eventId: String, isoDate: String?, precision: DatePrecision) {
        entities.setEventDate(eventId, isoDate, precision.name, now())
    }

    override suspend fun detachSource(eventId: String, recordId: String) {
        entities.detachEventSource(eventId, recordId)
    }

    override fun observeReview(): Flow<List<ReviewItem>> = dao.reviewItems().map { rows ->
        rows.map { row ->
            val kind = ReviewKind.valueOf(row.kind)
            ReviewItem(
                kind = kind,
                id = row.id,
                title = row.title,
                subtitle = if (kind == ReviewKind.EVENT) {
                    eventDateLabel(
                        parseDate(row.dateValue),
                        precision(row.datePrecision),
                    )
                } else {
                    row.subtitle
                },
            )
        }
    }

    override suspend fun confirm(item: ReviewItem) = changeReview(item, CONFIRMED, now())

    override suspend fun discard(item: ReviewItem) {
        when (item.kind) {
            ReviewKind.LINK -> item.id.split("|").takeIf { it.size == 2 }?.let { parts ->
                entities.deleteLink(parts[0], parts[1])
            }
            ReviewKind.RELATION -> entities.deleteRelationship(item.id)
            ReviewKind.EVENT -> entities.deleteEvent(item.id)
        }
    }

    private suspend fun changeReview(item: ReviewItem, state: String, now: Long) {
        when (item.kind) {
            ReviewKind.LINK -> item.id.split("|").takeIf { it.size == 2 }?.let { parts ->
                entities.setLinkReview(parts[0], parts[1], state)
            }
            ReviewKind.RELATION -> entities.setRelationshipReview(item.id, state)
            ReviewKind.EVENT -> entities.setEventReview(item.id, state, now)
        }
    }

    private fun withRelated(rows: List<EventRow>): Flow<List<TimelineEvent>> {
        val ids = rows.map { it.id }
        if (ids.isEmpty()) return flowOf(emptyList())
        return combine(dao.eventEntities(ids), dao.eventSources(ids)) { links, sources ->
            rows.map { row ->
                val participants = links.filter { it.eventId == row.id && it.role != PLACE }
                    .map { it.toParticipant() }
                val place = links.firstOrNull { it.eventId == row.id && it.role == PLACE }
                    ?.toParticipant()
                TimelineEvent(
                    id = row.id,
                    title = row.title,
                    summary = row.summary,
                    date = parseDate(row.eventDate),
                    precision = precision(row.datePrecision),
                    coverUri = row.coverUri,
                    origin = origin(row.origin),
                    suggested = row.reviewState == SUGGESTED,
                    participants = participants,
                    place = place,
                    sources = sources.filter { it.eventId == row.id }.map(::toSource),
                )
            }
        }
    }

    private fun toNode(row: ConnectionRow) = ConnectionNode(
        id = row.id,
        name = row.name,
        type = type(row.type),
        avatar = AvatarStyle(row.avatarModel, row.avatarBackground, row.skinColor, row.hairColor, row.clothingColor),
        recordCount = row.recordCount,
        relationLabel = row.label,
        origin = origin(row.origin),
    )

    private fun EventEntityRow.toParticipant() = Participant(entityId, name, avatar())

    private fun EventEntityRow.avatar() =
        AvatarStyle(avatarModel, avatarBackground, skinColor, hairColor, clothingColor)

    private fun toSource(row: EventSourceRow) = EventSource(
        recordId = row.recordId,
        preview = row.preview,
        recordedOn = parseDate(row.diaryDate),
        hasAudio = row.recordingId != null,
    )

    private fun type(value: String): EntityType =
        runCatching { EntityType.valueOf(value) }.getOrDefault(EntityType.PERSON)

    private fun origin(value: String): RelationOrigin =
        runCatching { RelationOrigin.valueOf(value) }.getOrDefault(RelationOrigin.CONFIRMED)

    private fun precision(value: String): DatePrecision =
        runCatching { DatePrecision.valueOf(value) }.getOrDefault(DatePrecision.UNKNOWN)

    private fun parseDate(value: String?): LocalDate? =
        value?.takeIf { it.length >= 10 }?.let { runCatching { LocalDate.parse(it.take(10)) }.getOrNull() }

    private companion object {
        const val LIMIT = 120
        const val CONFIRMED = "CONFIRMED"
        const val SUGGESTED = "SUGGESTED"
        const val PLACE = "PLACE"
    }
}
