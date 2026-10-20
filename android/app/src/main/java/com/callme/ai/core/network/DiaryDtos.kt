package com.callme.ai.core.network

import com.callme.ai.features.conversations.domain.DiarySnapshot
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/** Body of the local snapshot sent with a turn; the server does not store it. */
@Serializable
data class DiarySnapshotDto(
    val entities: List<DiaryEntityDto>,
    val events: List<DiaryEventDto>,
    val draft: String = "",
    val today: String? = null,
)

@Serializable
data class DiaryEntityDto(
    val id: String,
    val kind: String,
    val name: String,
    val relation: String = "",
)

@Serializable
data class DiaryEventDto(
    val id: String,
    val title: String,
    @SerialName("event_date") val eventDate: String? = null,
    val precision: String = "unknown",
)

/** Maps the domain snapshot to the wire format, lowercasing the enum names. */
fun DiarySnapshot.toDto(): DiarySnapshotDto = DiarySnapshotDto(
    entities = entities.map {
        DiaryEntityDto(id = it.id, kind = it.type.name.lowercase(), name = it.name, relation = it.relation)
    },
    events = events.map {
        DiaryEventDto(
            id = it.id,
            title = it.title,
            eventDate = it.date?.takeIf { _ -> it.precision.name != "UNKNOWN" },
            precision = it.precision.name.lowercase(),
        )
    },
    today = today,
)
