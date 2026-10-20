package com.callme.ai.devtools

import androidx.room.RoomDatabase
import androidx.sqlite.db.SimpleSQLiteQuery
import android.database.Cursor

/**
 * Routes the bridge calls made by the studio panel.
 *
 * Only the panel's routes exist: read the app state, edit one entity, and store
 * or reset manual map positions. Everything else answers 404.
 */
class DevRequest(private val db: RoomDatabase) {

    fun answer(method: String, path: String, body: String): DevResponse = when {
        method == "OPTIONS" -> DevResponse(200, "{}")
        method == "GET" && path == "/health" -> DevResponse(200, """{"ok":true}""")
        method == "GET" && path == "/state" -> DevResponse(200, DevState(db).read())
        method == "POST" && path.startsWith("/entities/") ->
            DevMutations(db).updateEntity(path.removePrefix("/entities/").trim('/'), body)
        method == "POST" && path == "/pins" -> DevMutations(db).pin(body)
        method == "POST" && path == "/pins/reset" -> DevMutations(db).clearPins()
        else -> DevResponse(404, """{"error":"unknown route"}""")
    }
}

/** Reads rows with a plain query so the bridge needs no extra DAO. */
internal fun RoomDatabase.rows(
    sql: String,
    arguments: List<Any?> = emptyList(),
    read: (Cursor) -> String,
): List<String> {
    val cursor = query(SimpleSQLiteQuery(sql, arguments.toTypedArray()))
    return cursor.use { open ->
        buildList { while (open.moveToNext()) add(read(open)) }
    }
}

/** Reads one scalar, or null when the query returns nothing. */
internal fun Cursor.text(column: String): String? =
    getColumnIndex(column).let { if (it < 0 || isNull(it)) null else getString(it) }

/** Joins row fragments into a JSON array. */
internal fun jsonArray(items: List<String>): String = items.joinToString(",", "[", "]")
