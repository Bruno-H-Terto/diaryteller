package com.callme.ai.core.database

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "record_metadata",
    foreignKeys = [ForeignKey(RecordEntity::class, ["id"], ["recordId"], ForeignKey.CASCADE)],
    indices = [Index("diaryDate"), Index("eventDate")],
)
data class RecordMetadataEntity(
    @PrimaryKey val recordId: String,
    val diaryDate: String,
    val coverUri: String?,
    val recordingId: String?,
    val eventDate: String?,
    val eventDatePrecision: String,
    val transcriptState: String,
)

data class RecordWithMetadata(
    val id: String,
    val currentVersionId: String,
    val createdAt: Long,
    val updatedAt: Long,
    val syncState: String,
    val remoteId: String?,
    val preview: String,
    val diaryDate: String?,
    val coverUri: String?,
    val recordingId: String?,
    val eventDate: String?,
    val eventDatePrecision: String?,
)


@Entity(tableName = "diary_entities", indices = [Index("type"), Index("name")])
data class DiaryEntity(
    @PrimaryKey val id: String,
    val type: String,
    val name: String,
    val avatarModel: String,
    val avatarBackground: Long,
    val skinColor: Long?,
    val hairColor: Long?,
    val clothingColor: Long?,
    val createdAt: Long,
    val updatedAt: Long,
)

@Entity(
    tableName = "record_entity_links",
    primaryKeys = ["recordId", "entityId"],
    foreignKeys = [
        ForeignKey(RecordEntity::class, ["id"], ["recordId"], ForeignKey.CASCADE),
        ForeignKey(DiaryEntity::class, ["id"], ["entityId"], ForeignKey.CASCADE),
    ],
    indices = [Index("entityId"), Index("recordId")],
)
data class RecordEntityLink(
    val recordId: String,
    val entityId: String,
    val origin: String,
    val reviewState: String,
)

@Entity(tableName = "events", indices = [Index("eventDate"), Index("updatedAt"), Index("reviewState")])
data class EventEntity(
    @PrimaryKey val id: String,
    val title: String,
    val summary: String,
    val eventDate: String?,
    val datePrecision: String,
    val coverUri: String?,
    val origin: String,
    val reviewState: String,
    val updatedAt: Long,
)

@Entity(
    tableName = "event_record_links",
    primaryKeys = ["eventId", "recordId"],
    foreignKeys = [
        ForeignKey(EventEntity::class, ["id"], ["eventId"], ForeignKey.CASCADE),
        ForeignKey(RecordEntity::class, ["id"], ["recordId"], ForeignKey.CASCADE),
    ],
    indices = [Index("recordId")],
)
data class EventRecordLink(val eventId: String, val recordId: String)

@Entity(
    tableName = "event_entity_links",
    primaryKeys = ["eventId", "entityId", "role"],
    foreignKeys = [
        ForeignKey(EventEntity::class, ["id"], ["eventId"], ForeignKey.CASCADE),
        ForeignKey(DiaryEntity::class, ["id"], ["entityId"], ForeignKey.CASCADE),
    ],
    indices = [Index("entityId")],
)
data class EventEntityLink(val eventId: String, val entityId: String, val role: String)

@Entity(
    tableName = "relationships",
    indices = [Index("fromEntityId"), Index("toEntityId"), Index("reviewState")],
)
data class RelationshipEntity(
    @PrimaryKey val id: String,
    val fromEntityId: String,
    val toEntityId: String,
    val label: String,
    val origin: String,
    val reviewState: String,
    val sourceRecordId: String?,
    val createdAt: Long,
)
