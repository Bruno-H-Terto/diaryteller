package com.callme.ai.core.database

import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase

/** Adds Diaryteller metadata without rewriting or deleting existing diary content. */
val MIGRATION_1_2 = object : Migration(1, 2) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("CREATE TABLE IF NOT EXISTS `record_metadata` (`recordId` TEXT NOT NULL, `diaryDate` TEXT NOT NULL, `coverUri` TEXT, `recordingId` TEXT, `eventDate` TEXT, `eventDatePrecision` TEXT NOT NULL, `transcriptState` TEXT NOT NULL, PRIMARY KEY(`recordId`), FOREIGN KEY(`recordId`) REFERENCES `records`(`id`) ON UPDATE NO ACTION ON DELETE CASCADE)")
        db.execSQL("CREATE INDEX IF NOT EXISTS `index_record_metadata_diaryDate` ON `record_metadata` (`diaryDate`)")
        db.execSQL("CREATE INDEX IF NOT EXISTS `index_record_metadata_eventDate` ON `record_metadata` (`eventDate`)")
        db.execSQL("INSERT OR IGNORE INTO record_metadata SELECT id, date(createdAt / 1000, 'unixepoch', 'localtime'), NULL, NULL, NULL, 'UNKNOWN', 'NONE' FROM records")
        db.execSQL("UPDATE record_metadata SET recordingId = (SELECT r.id FROM recordings r WHERE r.recordId = record_metadata.recordId LIMIT 1) WHERE recordingId IS NULL")
        db.execSQL("CREATE TABLE IF NOT EXISTS `diary_entities` (`id` TEXT NOT NULL, `type` TEXT NOT NULL, `name` TEXT NOT NULL, `avatarModel` TEXT NOT NULL, `avatarBackground` INTEGER NOT NULL, `skinColor` INTEGER, `hairColor` INTEGER, `clothingColor` INTEGER, `createdAt` INTEGER NOT NULL, `updatedAt` INTEGER NOT NULL, PRIMARY KEY(`id`))")
        db.execSQL("CREATE INDEX IF NOT EXISTS `index_diary_entities_type` ON `diary_entities` (`type`)")
        db.execSQL("CREATE INDEX IF NOT EXISTS `index_diary_entities_name` ON `diary_entities` (`name`)")
        db.execSQL("CREATE TABLE IF NOT EXISTS `record_entity_links` (`recordId` TEXT NOT NULL, `entityId` TEXT NOT NULL, `origin` TEXT NOT NULL, `reviewState` TEXT NOT NULL, PRIMARY KEY(`recordId`, `entityId`), FOREIGN KEY(`recordId`) REFERENCES `records`(`id`) ON UPDATE NO ACTION ON DELETE CASCADE, FOREIGN KEY(`entityId`) REFERENCES `diary_entities`(`id`) ON UPDATE NO ACTION ON DELETE CASCADE)")
        db.execSQL("CREATE INDEX IF NOT EXISTS `index_record_entity_links_entityId` ON `record_entity_links` (`entityId`)")
        db.execSQL("CREATE INDEX IF NOT EXISTS `index_record_entity_links_recordId` ON `record_entity_links` (`recordId`)")
        createEventTables(db)
        createRelationships(db)
    }

    private fun createEventTables(db: SupportSQLiteDatabase) {
        db.execSQL("CREATE TABLE IF NOT EXISTS `events` (`id` TEXT NOT NULL, `title` TEXT NOT NULL, `summary` TEXT NOT NULL, `eventDate` TEXT, `datePrecision` TEXT NOT NULL, `coverUri` TEXT, `origin` TEXT NOT NULL, `reviewState` TEXT NOT NULL, `updatedAt` INTEGER NOT NULL, PRIMARY KEY(`id`))")
        db.execSQL("CREATE INDEX IF NOT EXISTS `index_events_eventDate` ON `events` (`eventDate`)")
        db.execSQL("CREATE INDEX IF NOT EXISTS `index_events_updatedAt` ON `events` (`updatedAt`)")
        db.execSQL("CREATE INDEX IF NOT EXISTS `index_events_reviewState` ON `events` (`reviewState`)")
        db.execSQL("CREATE TABLE IF NOT EXISTS `event_record_links` (`eventId` TEXT NOT NULL, `recordId` TEXT NOT NULL, PRIMARY KEY(`eventId`, `recordId`), FOREIGN KEY(`eventId`) REFERENCES `events`(`id`) ON UPDATE NO ACTION ON DELETE CASCADE, FOREIGN KEY(`recordId`) REFERENCES `records`(`id`) ON UPDATE NO ACTION ON DELETE CASCADE)")
        db.execSQL("CREATE INDEX IF NOT EXISTS `index_event_record_links_recordId` ON `event_record_links` (`recordId`)")
        db.execSQL("CREATE TABLE IF NOT EXISTS `event_entity_links` (`eventId` TEXT NOT NULL, `entityId` TEXT NOT NULL, `role` TEXT NOT NULL, PRIMARY KEY(`eventId`, `entityId`, `role`), FOREIGN KEY(`eventId`) REFERENCES `events`(`id`) ON UPDATE NO ACTION ON DELETE CASCADE, FOREIGN KEY(`entityId`) REFERENCES `diary_entities`(`id`) ON UPDATE NO ACTION ON DELETE CASCADE)")
        db.execSQL("CREATE INDEX IF NOT EXISTS `index_event_entity_links_entityId` ON `event_entity_links` (`entityId`)")
    }

    private fun createRelationships(db: SupportSQLiteDatabase) {
        db.execSQL("CREATE TABLE IF NOT EXISTS `relationships` (`id` TEXT NOT NULL, `fromEntityId` TEXT NOT NULL, `toEntityId` TEXT NOT NULL, `label` TEXT NOT NULL, `origin` TEXT NOT NULL, `reviewState` TEXT NOT NULL, `sourceRecordId` TEXT, `createdAt` INTEGER NOT NULL, PRIMARY KEY(`id`))")
        db.execSQL("CREATE INDEX IF NOT EXISTS `index_relationships_fromEntityId` ON `relationships` (`fromEntityId`)")
        db.execSQL("CREATE INDEX IF NOT EXISTS `index_relationships_toEntityId` ON `relationships` (`toEntityId`)")
        db.execSQL("CREATE INDEX IF NOT EXISTS `index_relationships_reviewState` ON `relationships` (`reviewState`)")
    }
}
