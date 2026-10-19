package com.callme.ai.core.database

import androidx.room.Database
import androidx.room.RoomDatabase

@Database(
    entities = [
        RecordEntity::class,
        RecordVersionEntity::class,
        SyncQueueEntity::class,
        RecordingEntity::class,
    ],
    version = 1,
    exportSchema = false,
)
abstract class CallMeDatabase : RoomDatabase() {
    abstract fun recordsDao(): RecordsDao
}
