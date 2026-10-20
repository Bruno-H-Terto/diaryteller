package com.callme.ai.features.records.adapters

import com.callme.ai.core.database.RecordVersionEntity
import com.callme.ai.core.database.RecordWithMetadata
import com.callme.ai.core.model.DatePrecision
import com.callme.ai.features.records.domain.Record
import com.callme.ai.features.records.domain.RecordSyncState
import com.callme.ai.features.records.domain.RecordVersion
import com.callme.ai.features.records.domain.VersionOrigin
import java.time.Instant
import java.time.ZoneId

/** Row to domain mapping kept next to the adapter that owns the schema. */
internal fun RecordWithMetadata.toRecord() = Record(
    id = id,
    currentVersionId = currentVersionId,
    createdAt = createdAt,
    updatedAt = updatedAt,
    syncState = runCatching { RecordSyncState.valueOf(syncState) }.getOrDefault(RecordSyncState.LOCAL),
    preview = preview,
    diaryDate = diaryDate ?: Instant.ofEpochMilli(createdAt)
        .atZone(ZoneId.systemDefault()).toLocalDate().toString(),
    coverUri = coverUri,
    recordingId = recordingId,
    eventDate = eventDate,
    eventDatePrecision = runCatching { DatePrecision.valueOf(eventDatePrecision.orEmpty()) }
        .getOrDefault(DatePrecision.UNKNOWN),
)

internal fun RecordVersionEntity.toVersion() = RecordVersion(
    id = id,
    recordId = recordId,
    number = number,
    content = content,
    origin = runCatching { VersionOrigin.valueOf(origin) }.getOrDefault(VersionOrigin.USER),
    baseVersionId = baseVersionId,
    createdAt = createdAt,
    confirmed = confirmed,
)

internal fun RecordVersion.toEntity() = RecordVersionEntity(
    id = id,
    recordId = recordId,
    number = number,
    content = content,
    origin = origin.name,
    baseVersionId = baseVersionId,
    createdAt = createdAt,
    confirmed = confirmed,
)
