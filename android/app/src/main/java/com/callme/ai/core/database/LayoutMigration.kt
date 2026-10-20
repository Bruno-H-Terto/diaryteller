package com.callme.ai.core.database

import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase

/** Adds the manual map layout written by the studio panel; nothing else changes. */
val MIGRATION_2_3 = object : Migration(2, 3) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL(
            "CREATE TABLE IF NOT EXISTS `map_pins` (`entityId` TEXT NOT NULL, `x` REAL NOT NULL, " +
                "`y` REAL NOT NULL, PRIMARY KEY(`entityId`))",
        )
    }
}
