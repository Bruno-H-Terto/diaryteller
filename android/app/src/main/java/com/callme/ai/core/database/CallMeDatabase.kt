package com.callme.ai.core.database

import androidx.room.Database
import androidx.room.RoomDatabase

@Database(
    entities = [
        RecordEntity::class,
        RecordVersionEntity::class,
        SyncQueueEntity::class,
        RecordingEntity::class,
        RecordMetadataEntity::class,
        DiaryEntity::class,
        RecordEntityLink::class,
        EventEntity::class,
        EventRecordLink::class,
        EventEntityLink::class,
        RelationshipEntity::class,
        MapPinEntity::class,
    ],
    version = 3,
    exportSchema = false,
)
abstract class CallMeDatabase : RoomDatabase() {
    abstract fun recordsDao(): RecordsDao
    abstract fun connectionsDao(): ConnectionsDao

    abstract fun entitiesDao(): EntitiesDao

    abstract fun mapPinDao(): MapPinDao

    abstract fun snapshotDao(): DiarySnapshotDao
}
