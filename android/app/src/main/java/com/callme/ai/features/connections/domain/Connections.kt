package com.callme.ai.features.connections.domain

import com.callme.ai.core.model.AvatarStyle
import com.callme.ai.core.model.DatePrecision
import com.callme.ai.core.model.capitalized
import com.callme.ai.core.model.dayLabel
import com.callme.ai.core.model.monthLabel
import com.callme.ai.features.entities.domain.EntityType
import com.callme.ai.features.entities.domain.RelationOrigin
import java.time.LocalDate
import java.time.YearMonth

/** One entity connected to the diary owner inside the selected period. */
data class ConnectionNode(
    val id: String,
    val name: String,
    val type: EntityType,
    val avatar: AvatarStyle,
    val recordCount: Int,
    val relationLabel: String,
    val origin: RelationOrigin,
)

/** Counts shown around the centre of the map. */
data class MapSummary(val records: Int, val audio: Int, val neighbours: Int)

data class TimelineEvent(
    val id: String,
    val title: String,
    val summary: String,
    val date: LocalDate?,
    val precision: DatePrecision,
    val coverUri: String?,
    val origin: RelationOrigin,
    val suggested: Boolean,
    val participants: List<Participant>,
    val place: Participant?,
    val sources: List<EventSource>,
)

data class Participant(
    val entityId: String,
    val name: String,
    val avatar: AvatarStyle,
)

/** One narrated record behind an event; the date shown is the recording date. */
data class EventSource(
    val recordId: String,
    val preview: String,
    val recordedOn: LocalDate?,
    val hasAudio: Boolean,
)

/** A suggestion the user still has to confirm or discard. */
data class ReviewItem(val kind: ReviewKind, val id: String, val title: String, val subtitle: String)

enum class ReviewKind { LINK, RELATION, EVENT }

/** Timeline month bucket with its days in reverse chronological order. */
data class TimelineMonth(
    val key: String,
    val label: String,
    val days: List<TimelineDay>,
    val eventCount: Int,
)

data class TimelineDay(
    val key: String,
    val date: LocalDate?,
    val label: String,
    val events: List<TimelineEvent>,
) {
}

/**
 * Groups events into months and days without inventing precision: a year-only
 * event is listed under its year, a month-only event under the month, and events
 * without a date go to a separate trailing bucket.
 */
fun groupTimeline(events: List<TimelineEvent>): List<TimelineMonth> {
    val placed = events.mapNotNull { event -> placement(event)?.let { event to it } }
    val months = placed.groupBy { it.second.monthKey }
        .values
        .sortedByDescending { group -> group.maxOf { it.second.order } }
        .map { group ->
            val days = group.groupBy { it.second.dayKey }
                .values
                .sortedByDescending { day -> day.maxOf { it.second.order } }
                .map { day ->
                    TimelineDay(
                        key = day.first().second.dayKey,
                        date = day.first().second.date,
                        label = day.first().second.dayLabel,
                        events = day.map { it.first },
                    )
                }
            TimelineMonth(
                key = group.first().second.monthKey,
                label = group.first().second.monthLabel,
                days = days,
                eventCount = group.size,
            )
        }
    val undated = events.filter { placement(it) == null }
    if (undated.isEmpty()) return months
    return months + TimelineMonth(
        key = UNDATED_KEY,
        label = "Sem data definida",
        days = listOf(TimelineDay(UNDATED_KEY, null, "Sem data definida", undated)),
        eventCount = undated.size,
    )
}

private data class Placement(
    val monthKey: String,
    val monthLabel: String,
    val dayKey: String,
    val dayLabel: String,
    val date: LocalDate,
    val order: LocalDate,
)

private fun placement(event: TimelineEvent): Placement? {
    val date = event.date ?: return null
    return when (event.precision) {
        DatePrecision.DAY -> Placement(
            monthKey = YearMonth.from(date).toString(),
            monthLabel = monthLabel(YearMonth.from(date)),
            dayKey = date.toString(),
            dayLabel = dayLabel(date),
            date = date,
            order = date,
        )
        DatePrecision.MONTH -> Placement(
            monthKey = YearMonth.from(date).toString(),
            monthLabel = monthLabel(YearMonth.from(date)),
            dayKey = "m-${YearMonth.from(date)}",
            dayLabel = "${monthLabel(YearMonth.from(date))} · mês informado",
            date = date,
            order = date,
        )
        DatePrecision.YEAR -> Placement(
            monthKey = "y-${date.year}",
            monthLabel = date.year.toString(),
            dayKey = "y-${date.year}",
            dayLabel = "${date.year} · ano informado",
            date = date,
            order = date,
        )
        DatePrecision.UNKNOWN -> null
    }
}

const val UNDATED_KEY = "sem-data"
