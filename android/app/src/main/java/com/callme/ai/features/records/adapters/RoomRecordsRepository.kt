package com.callme.ai.features.records.adapters

import com.callme.ai.core.database.RecordEntity
import com.callme.ai.core.database.RecordVersionEntity
import com.callme.ai.core.database.RecordsDao
import com.callme.ai.core.database.SyncQueueEntity
import com.callme.ai.features.records.application.RecordsRepository
import com.callme.ai.features.records.domain.Record
import com.callme.ai.features.records.domain.RecordSyncState
import com.callme.ai.features.records.domain.RecordVersion
import com.callme.ai.features.records.domain.VersionOrigin
import com.callme.ai.features.records.domain.Versioning
import java.time.Instant
import java.util.UUID
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

class RoomRecordsRepository(
    private val dao: RecordsDao,
    private val now: () -> Long = { Instant.now().toEpochMilli() },
    private val newId: () -> String = { UUID.randomUUID().toString() },
) : RecordsRepository {

    override fun observeRecords(): Flow<List<Record>> =
        dao.observeRecords().map { rows -> rows.map(::toRecord) }

    override fun observeVersions(recordId: String): Flow<List<RecordVersion>> =
        dao.observeVersions(recordId).map { rows -> rows.map(::toVersion) }

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
        val number = Versioning.nextNumber(dao.versions(recordId).map(::toVersion))
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
        val target = dao.version(versionId)?.let(::toVersion) ?: return ""
        val restored = Versioning.restored(target, record.currentVersionId, newId(), now())
        val versions = dao.versions(recordId).map(::toVersion)
        val numbered = restored.copy(number = Versioning.nextNumber(versions))
        dao.insertVersion(toEntity(numbered))
        dao.pointToVersion(recordId, numbered.id, numbered.createdAt)
        dao.updatePreview(recordId, numbered.content.take(120), numbered.createdAt)
        enqueue(recordId, "version")
        return numbered.id
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

    private fun toRecord(row: RecordEntity) = Record(
        id = row.id,
        currentVersionId = row.currentVersionId,
        createdAt = row.createdAt,
        updatedAt = row.updatedAt,
        syncState = runCatching { RecordSyncState.valueOf(row.syncState) }.getOrDefault(RecordSyncState.LOCAL),
        preview = row.preview,
    )

    private fun toVersion(row: RecordVersionEntity) = RecordVersion(
        id = row.id,
        recordId = row.recordId,
        number = row.number,
        content = row.content,
        origin = runCatching { VersionOrigin.valueOf(row.origin) }.getOrDefault(VersionOrigin.USER),
        baseVersionId = row.baseVersionId,
        createdAt = row.createdAt,
        confirmed = row.confirmed,
    )

    private fun toEntity(version: RecordVersion) = RecordVersionEntity(
        id = version.id,
        recordId = version.recordId,
        number = version.number,
        content = version.content,
        origin = version.origin.name,
        baseVersionId = version.baseVersionId,
        createdAt = version.createdAt,
        confirmed = version.confirmed,
    )
}
