package com.callme.ai.core.database

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(tableName = "records", indices = [Index("createdAt")])
data class RecordEntity(
    @PrimaryKey val id: String,
    val currentVersionId: String,
    val createdAt: Long,
    val updatedAt: Long,
    val syncState: String,
    val remoteId: String?,
    val preview: String,
)

@Entity(
    tableName = "record_versions",
    foreignKeys = [
        ForeignKey(
            entity = RecordEntity::class,
            parentColumns = ["id"],
            childColumns = ["recordId"],
            onDelete = ForeignKey.CASCADE,
        ),
    ],
    indices = [Index("recordId"), Index(value = ["recordId", "number"], unique = true)],
)
data class RecordVersionEntity(
    @PrimaryKey val id: String,
    val recordId: String,
    val number: Int,
    val content: String,
    val origin: String,
    val baseVersionId: String?,
    val createdAt: Long,
    val confirmed: Boolean,
)

@Entity(tableName = "sync_queue", indices = [Index("entityId"), Index("state")])
data class SyncQueueEntity(
    @PrimaryKey val id: String,
    val entityType: String,
    val entityId: String,
    val operation: String,
    val attempts: Int,
    val nextAttemptAt: Long,
    val state: String,
    val lastError: String?,
)

@Entity(tableName = "recordings", indices = [Index("createdAt")])
data class RecordingEntity(
    @PrimaryKey val id: String,
    val createdAt: Long,
    val durationMs: Long,
    val sizeBytes: Long,
    val fileName: String,
    val state: String,
    val recordId: String?,
)
