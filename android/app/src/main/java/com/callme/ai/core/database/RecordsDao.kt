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

    @Query(
        """
        SELECT r.*, m.diaryDate, m.coverUri, m.recordingId, m.eventDate, m.eventDatePrecision
        FROM records r
        LEFT JOIN record_metadata m ON m.recordId = r.id
        ORDER BY COALESCE(m.diaryDate, date(r.createdAt / 1000, 'unixepoch')) DESC,
                 r.createdAt DESC
        """,
    )
    fun observeDiaryRecords(): Flow<List<RecordWithMetadata>>

    @Query(
        """
        SELECT r.*, m.diaryDate, m.coverUri, m.recordingId, m.eventDate, m.eventDatePrecision
        FROM records r LEFT JOIN record_metadata m ON m.recordId = r.id
        WHERE r.id = :recordId
        """,
    )
    fun observeRecord(recordId: String): Flow<RecordWithMetadata?>

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
    suspend fun insertMetadata(metadata: RecordMetadataEntity)

    @Query("SELECT * FROM record_metadata WHERE recordId = :recordId")
    suspend fun metadata(recordId: String): RecordMetadataEntity?

    @Query("UPDATE record_metadata SET coverUri = :coverUri WHERE recordId = :recordId")
    suspend fun updateCover(recordId: String, coverUri: String?)

    @Query("UPDATE record_metadata SET recordingId = :recordingId WHERE recordId = :recordId")
    suspend fun updateRecording(recordId: String, recordingId: String?)

    @Query(
        """
        UPDATE record_metadata SET eventDate = :date, eventDatePrecision = :precision
        WHERE recordId = :recordId
        """,
    )
    suspend fun updateEventDate(recordId: String, date: String?, precision: String)

    @Query("SELECT * FROM recordings ORDER BY createdAt DESC")
    suspend fun recordings(): List<RecordingEntity>

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

    @Query("DELETE FROM record_metadata")
    suspend fun clearMetadata()

    @Query("DELETE FROM records WHERE id LIKE 'sample-%'")
    suspend fun deleteSampleRecords()

    @Query("SELECT recordingId FROM record_metadata WHERE recordId LIKE 'sample-%' AND recordingId IS NOT NULL")
    suspend fun sampleRecordingIds(): List<String>

    @Query("SELECT COUNT(*) FROM records WHERE id LIKE 'sample-%'")
    fun observeSampleCount(): Flow<Int>

    @Transaction
    suspend fun clearAll() {
        clearRecordings()
        clearMetadata()
        clearVersions()
        clearRecords()
        clearQueue()
    }

    @Insert
    suspend fun enqueue(item: SyncQueueEntity)

    @Insert
    suspend fun insertRecording(recording: RecordingEntity)


    @Query("SELECT * FROM recordings WHERE id = :id")
    suspend fun recording(id: String): RecordingEntity?

    @Query("UPDATE recordings SET recordId = :recordId WHERE id = :id")
    suspend fun attachRecording(id: String, recordId: String)

    @Query("DELETE FROM recordings WHERE id = :id")
    suspend fun deleteRecording(id: String)

    @Query("DELETE FROM recordings")
    suspend fun clearRecordings()

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
