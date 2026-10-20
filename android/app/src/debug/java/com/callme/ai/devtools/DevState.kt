package com.callme.ai.devtools

import androidx.room.RoomDatabase
import android.database.Cursor

/**
 * Serializes the on-device diary state the studio panel displays.
 *
 * It reads counts and identifiers only; diary texts are included because the
 * panel is a local, developer-only surface, and media bytes are never touched.
 */
class DevState(private val db: RoomDatabase) {

    fun read(): String = buildString {
        append('{')
        append("\"records\":").append(jsonArray(records()))
        append(",\"entities\":").append(jsonArray(entities()))
        append(",\"events\":").append(jsonArray(events()))
        append(",\"links\":").append(jsonArray(links()))
        append(",\"pins\":").append(jsonArray(pins()))
        append('}')
    }

    private fun records(): List<String> = db.rows(
        """
        SELECT r.id, r.preview, r.updatedAt, v.content, m.eventDate, m.eventDatePrecision, m.recordingId, m.diaryDate
        FROM records r
        LEFT JOIN record_versions v ON v.id = r.currentVersionId
        LEFT JOIN record_metadata m ON m.recordId = r.id
        ORDER BY r.updatedAt DESC LIMIT $LIMIT
        """.trimIndent(),
    ) { row ->
        """{"id":${quote(row.row("id"))},"title":${quote(row.headline("content"))},""" +
            """"preview":${quote(row.row("preview"))},"updatedAt":${row.long("updatedAt")},""" +
            """"eventDate":${nullable(row.text("eventDate"))},"precision":${nullable(row.text("eventDatePrecision"))},""" +
            """"hasAudio":${row.text("recordingId") != null}}"""
    }

    private fun entities(): List<String> = db.rows(
        """
        SELECT id, type, name, avatarModel, avatarBackground, skinColor, hairColor, clothingColor
        FROM diary_entities ORDER BY type, name COLLATE NOCASE LIMIT $LIMIT
        """.trimIndent(),
    ) { row ->
        """{"id":${quote(row.row("id"))},"type":${quote(row.row("type"))},"name":${quote(row.row("name"))},""" +
            """"model":${quote(row.row("avatarModel"))},""" +
            """"background":${row.long("avatarBackground")},"skin":${row.text("skinColor")},""" +
            """"hair":${row.text("hairColor")},"clothing":${row.text("clothingColor")}}"""
    }

    private fun events(): List<String> = db.rows(
        "SELECT id, title, eventDate, datePrecision, reviewState FROM events ORDER BY eventDate DESC LIMIT $LIMIT",
    ) { row ->
        """{"id":${quote(row.row("id"))},"title":${quote(row.headline("content"))},""" +
            """"eventDate":${nullable(row.text("eventDate"))},"precision":${nullable(row.text("eventDatePrecision"))},""" +
            """"state":${quote(row.row("reviewState"))}}"""
    }

    private fun links(): List<String> = db.rows(
        "SELECT recordId, entityId, origin, reviewState FROM record_entity_links LIMIT $LIMIT",
    ) { row ->
        """{"recordId":${quote(row.row("recordId"))},"entityId":${quote(row.row("entityId"))},""" +
            """"origin":${quote(row.row("origin"))},"state":${quote(row.row("reviewState"))}}"""
    }

    private fun pins(): List<String> = db.rows("SELECT entityId, x, y FROM map_pins") { row ->
        """{"entityId":${quote(row.row("entityId"))},"x":${row.decimal("x")},""" +
            """"y":${row.decimal("y")}}"""
    }

    private fun Cursor.row(column: String): String = text(column) ?: ""

    private fun Cursor.long(column: String): Long = getLong(index(column))

    private fun Cursor.decimal(column: String): Float = getFloat(index(column))

    private fun Cursor.index(column: String): Int =
        getColumnIndex(column).also { check(it >= 0) { "column $column missing" } }

    /** First line of the entry text, short enough for a table cell. */
    private fun Cursor.headline(column: String): String =
        row(column).lineSequence().firstOrNull { it.isNotBlank() }?.take(60) ?: "Sem título"

    private fun nullable(value: String?): String = value?.let(::quote) ?: "null"

    private companion object {
        const val LIMIT = 200
    }
}
