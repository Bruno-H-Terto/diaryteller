package com.callme.ai.features.records.application

import com.callme.ai.core.model.DatePrecision
import com.callme.ai.features.records.domain.Record
import com.callme.ai.features.records.domain.RecordVersion
import kotlinx.coroutines.flow.Flow

interface RecordsRepository {
    fun observeRecords(): Flow<List<Record>>
    fun observeRecord(recordId: String): Flow<Record?>
    fun observeVersions(recordId: String): Flow<List<RecordVersion>>

    suspend fun createDraft(): String

    /** Creates a record whose version 1 is already confirmed (for example a transcript). */
    suspend fun createRecord(content: String): String

    /** Current confirmed text of a record; null when it does not exist. */
    suspend fun currentContent(recordId: String): String?
    suspend fun updateDraft(recordId: String, content: String)
    suspend fun confirmDraft(recordId: String, content: String)
    suspend fun addVersion(recordId: String, content: String): String
    suspend fun restoreVersion(recordId: String, versionId: String): String
    /** Stores the date of the narrated event with its explicit precision. */
    suspend fun setEventDate(recordId: String, isoDate: String?, precision: DatePrecision)
    suspend fun deleteRecord(recordId: String)
    suspend fun clearAccountData()
}
