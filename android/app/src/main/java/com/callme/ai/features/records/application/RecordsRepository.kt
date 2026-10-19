package com.callme.ai.features.records.application

import com.callme.ai.features.records.domain.Record
import com.callme.ai.features.records.domain.RecordVersion
import kotlinx.coroutines.flow.Flow

interface RecordsRepository {
    fun observeRecords(): Flow<List<Record>>
    fun observeVersions(recordId: String): Flow<List<RecordVersion>>

    suspend fun createDraft(): String

    /** Creates a record whose version 1 is already confirmed (for example a transcript). */
    suspend fun createRecord(content: String): String
    suspend fun updateDraft(recordId: String, content: String)
    suspend fun confirmDraft(recordId: String, content: String)
    suspend fun addVersion(recordId: String, content: String): String
    suspend fun restoreVersion(recordId: String, versionId: String): String
    suspend fun deleteRecord(recordId: String)
    suspend fun clearAccountData()
}
