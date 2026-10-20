package com.callme.ai.features.records.adapters

import com.callme.ai.core.database.RecordEntity
import com.callme.ai.core.database.RecordMetadataEntity
import com.callme.ai.core.database.RecordWithMetadata
import com.callme.ai.core.database.RecordVersionEntity
import com.callme.ai.core.database.RecordsDao
import com.callme.ai.core.database.SyncQueueEntity
import com.callme.ai.features.records.application.RecordsRepository
import com.callme.ai.features.records.domain.Record
import com.callme.ai.features.records.domain.RecordSyncState
import com.callme.ai.features.records.domain.RecordVersion
import com.callme.ai.features.records.domain.VersionOrigin
import com.callme.ai.features.records.domain.Versioning
import com.callme.ai.core.model.DatePrecision
import java.time.Instant
import java.time.ZoneId
import java.util.UUID
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

class RoomRecordsRepository(
    private val dao: RecordsDao,
    private val now: () -> Long = { Instant.now().toEpochMilli() },
    private val newId: () -> String = { UUID.randomUUID().toString() },
) : RecordsRepository {

    override fun observeRecords(): Flow<List<Record>> =
        dao.observeDiaryRecords().map { rows -> rows.map { it.toRecord() } }

    override fun observeRecord(recordId: String): Flow<Record?> =
        dao.observeRecord(recordId).map { row -> row?.let { it.toRecord() } }

    override fun observeVersions(recordId: String): Flow<List<RecordVersion>> =
        dao.observeVersions(recordId).map { rows -> rows.map { it.toVersion() } }

    override suspend fun createDraft(): String {
        val recordId = newId()
        val versionId = newId()
        val moment = now()
        dao.insertRecord(
            RecordEntity(
                id = recordId,
                currentVersionId = versionId,
                createdAt = moment,
                updatedAt = moment,
                syncState = RecordSyncState.LOCAL.name,
                remoteId = null,
                preview = "",
            ),
        )
        dao.insertMetadata(
            RecordMetadataEntity(
                recordId = recordId,
                diaryDate = Instant.ofEpochMilli(moment).atZone(ZoneId.systemDefault())
                    .toLocalDate().toString(),
                coverUri = null,
                recordingId = null,
                eventDate = null,
                eventDatePrecision = "UNKNOWN",
                transcriptState = "NONE",
            ),
        )
        dao.insertVersion(
            RecordVersionEntity(
                id = versionId,
                recordId = recordId,
                number = 1,
                content = "",
                origin = VersionOrigin.USER.name,
                baseVersionId = null,
                createdAt = moment,
                confirmed = false,
            ),
        )
        return recordId
    }

    override suspend fun createRecord(content: String): String {
        val recordId = createDraft()
        confirmDraft(recordId, content)
        return recordId
    }

    override suspend fun currentContent(recordId: String): String? {
        val record = dao.record(recordId) ?: return null
        return dao.version(record.currentVersionId)?.content
    }

    override suspend fun updateDraft(recordId: String, content: String) {
        val record = dao.record(recordId) ?: return
        val version = dao.version(record.currentVersionId) ?: return
        if (version.confirmed) return
        dao.updateVersionContent(version.id, content)
        dao.updatePreview(recordId, content.take(120), now())
    }

    override suspend fun confirmDraft(recordId: String, content: String) {
        val record = dao.record(recordId) ?: return
        val version = dao.version(record.currentVersionId) ?: return
        if (version.confirmed) {
            addVersion(recordId, content)
            return
        }
        dao.confirmVersion(version.id, content)
        dao.updatePreview(recordId, content.take(120), now())
        dao.updateSyncState(recordId, RecordSyncState.PENDING.name, null)
        enqueue(recordId, "create")
    }

    override suspend fun addVersion(recordId: String, content: String): String {
        val record = dao.record(recordId) ?: return ""
        val number = Versioning.nextNumber(dao.versions(recordId).map { it.toVersion() })
        val versionId = newId()
        val moment = now()
        dao.insertVersion(
            RecordVersionEntity(
                id = versionId,
                recordId = recordId,
                number = number,
                content = content,
                origin = VersionOrigin.USER.name,
                baseVersionId = record.currentVersionId,
                createdAt = moment,
                confirmed = true,
            ),
        )
        dao.pointToVersion(recordId, versionId, moment)
        dao.updatePreview(recordId, content.take(120), moment)
        dao.updateSyncState(recordId, RecordSyncState.PENDING.name, record.remoteId)
        enqueue(recordId, "version")
        return versionId
    }

    override suspend fun restoreVersion(recordId: String, versionId: String): String {
        val record = dao.record(recordId) ?: return ""
        val target = dao.version(versionId)?.let { it.toVersion() } ?: return ""
        val restored = Versioning.restored(target, record.currentVersionId, newId(), now())
        val versions = dao.versions(recordId).map { it.toVersion() }
        val numbered = restored.copy(number = Versioning.nextNumber(versions))
        dao.insertVersion(numbered.toEntity())
        dao.pointToVersion(recordId, numbered.id, numbered.createdAt)
        dao.updatePreview(recordId, numbered.content.take(120), numbered.createdAt)
        enqueue(recordId, "version")
        return numbered.id
    }

    override suspend fun setEventDate(recordId: String, isoDate: String?, precision: DatePrecision) {
        dao.updateEventDate(recordId, isoDate, precision.name)
    }

    override suspend fun deleteRecord(recordId: String) {
        dao.deleteWithVersions(recordId)
    }

    override suspend fun clearAccountData() {
        dao.clearAll()
    }

    private suspend fun enqueue(recordId: String, operation: String) {
        dao.enqueue(
            SyncQueueEntity(
                id = newId(),
                entityType = "record",
                entityId = recordId,
                operation = operation,
                attempts = 0,
                nextAttemptAt = now(),
                state = "PENDING",
                lastError = null,
            ),
        )
    }
}
