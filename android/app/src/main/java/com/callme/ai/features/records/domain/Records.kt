package com.callme.ai.features.records.domain

import com.callme.ai.core.model.DatePrecision

enum class VersionOrigin { USER, AI, RESTORE, IMPORT }

enum class RecordSyncState { LOCAL, PENDING, SYNCING, SYNCED, FAILED, CONFLICT }

data class Record(
    val id: String,
    val currentVersionId: String,
    val createdAt: Long,
    val updatedAt: Long,
    val syncState: RecordSyncState,
    val preview: String,
    val diaryDate: String = "",
    val coverUri: String? = null,
    val recordingId: String? = null,
    val eventDate: String? = null,
    val eventDatePrecision: DatePrecision = DatePrecision.UNKNOWN,
)

data class RecordVersion(
    val id: String,
    val recordId: String,
    val number: Int,
    val content: String,
    val origin: VersionOrigin,
    val baseVersionId: String?,
    val createdAt: Long,
    val confirmed: Boolean,
)

/** Version rules that must hold regardless of UI or storage. */
object Versioning {
    fun nextNumber(existing: List<RecordVersion>): Int = (existing.maxOfOrNull { it.number } ?: 0) + 1

    fun restored(target: RecordVersion, baseVersionId: String, id: String, now: Long): RecordVersion =
        target.copy(
            id = id,
            number = 0,
            origin = VersionOrigin.RESTORE,
            baseVersionId = baseVersionId,
            createdAt = now,
            confirmed = true,
        )
}
