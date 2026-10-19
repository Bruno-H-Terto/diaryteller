package com.callme.ai.core.database

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query
import androidx.room.Transaction
import kotlinx.coroutines.flow.Flow

@Dao
interface RecordsDao {
    @Query("SELECT * FROM records ORDER BY updatedAt DESC")
    fun observeRecords(): Flow<List<RecordEntity>>

    @Query("SELECT * FROM records WHERE id = :recordId")
    suspend fun record(recordId: String): RecordEntity?

    @Query("SELECT * FROM record_versions WHERE recordId = :recordId ORDER BY number ASC")
    fun observeVersions(recordId: String): Flow<List<RecordVersionEntity>>

    @Query("SELECT * FROM record_versions WHERE recordId = :recordId ORDER BY number ASC")
    suspend fun versions(recordId: String): List<RecordVersionEntity>

    @Query("SELECT MAX(number) FROM record_versions WHERE recordId = :recordId")
    suspend fun maxVersionNumber(recordId: String): Int?

    @Insert
    suspend fun insertRecord(record: RecordEntity)

    @Insert
    suspend fun insertVersion(version: RecordVersionEntity)

    @Query("SELECT * FROM record_versions WHERE id = :versionId")
    suspend fun version(versionId: String): RecordVersionEntity?

    @Query("UPDATE record_versions SET content = :content WHERE id = :versionId")
    suspend fun updateVersionContent(versionId: String, content: String)

    @Query("UPDATE record_versions SET content = :content, confirmed = 1 WHERE id = :versionId")
    suspend fun confirmVersion(versionId: String, content: String)

    @Query("UPDATE records SET currentVersionId = :versionId, updatedAt = :now WHERE id = :recordId")
    suspend fun pointToVersion(recordId: String, versionId: String, now: Long)

    @Query("UPDATE records SET syncState = :state, remoteId = :remoteId WHERE id = :recordId")
    suspend fun updateSyncState(recordId: String, state: String, remoteId: String?)

    @Query("UPDATE records SET preview = :preview, updatedAt = :now WHERE id = :recordId")
    suspend fun updatePreview(recordId: String, preview: String, now: Long)

    @Query("DELETE FROM record_versions")
    suspend fun clearVersions()

    @Query("DELETE FROM records")
    suspend fun clearRecords()

    @Query("DELETE FROM sync_queue")
    suspend fun clearQueue()

    @Transaction
    suspend fun clearAll() {
        clearVersions()
        clearRecords()
        clearQueue()
    }

    @Insert
    suspend fun enqueue(item: SyncQueueEntity)

    @Query("SELECT * FROM sync_queue WHERE state = 'PENDING' AND nextAttemptAt <= :now ORDER BY nextAttemptAt LIMIT :limit")
    suspend fun dueQueue(now: Long, limit: Int): List<SyncQueueEntity>

    @Query("UPDATE sync_queue SET state = :state, attempts = :attempts, nextAttemptAt = :next, lastError = :error WHERE id = :id")
    suspend fun updateQueue(id: String, state: String, attempts: Int, next: Long, error: String?)

    @Query("DELETE FROM record_versions WHERE recordId = :recordId")
    suspend fun deleteVersions(recordId: String)

    @Query("DELETE FROM records WHERE id = :recordId")
    suspend fun deleteRecord(recordId: String)

    @Transaction
    suspend fun deleteWithVersions(recordId: String) {
        deleteVersions(recordId)
        deleteRecord(recordId)
    }
}
