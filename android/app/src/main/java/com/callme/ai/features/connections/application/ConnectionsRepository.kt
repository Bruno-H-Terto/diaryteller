package com.callme.ai.features.connections.application

import com.callme.ai.core.model.DatePrecision
import com.callme.ai.core.model.Period
import com.callme.ai.features.connections.domain.ConnectionNode
import com.callme.ai.features.connections.domain.MapSummary
import com.callme.ai.features.connections.domain.ReviewItem
import com.callme.ai.features.connections.domain.TimelineEvent
import com.callme.ai.features.entities.domain.EntityType
import kotlinx.coroutines.flow.Flow

/** Map data plus the totals that explain it. */
data class MapData(val nodes: List<ConnectionNode>, val summary: MapSummary)

/**
 * Read model of the connections area. Frequency always counts distinct records
 * inside the period, so repeated mentions and extra versions never inflate it.
 */
interface ConnectionsRepository {
    fun observeMap(period: Period, type: EntityType?, query: String): Flow<MapData>
    fun observeTimeline(period: Period, limit: Int): Flow<List<TimelineEvent>>
    fun observeReview(): Flow<List<ReviewItem>>
    fun observeEvent(eventId: String): Flow<TimelineEvent?>
    suspend fun setEventDate(eventId: String, isoDate: String?, precision: DatePrecision)
    suspend fun detachSource(eventId: String, recordId: String)
    suspend fun confirm(item: ReviewItem)
    suspend fun discard(item: ReviewItem)
}
