package com.callme.ai.devtools

import androidx.room.RoomDatabase
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive

/**
 * Applies the edits the studio panel can make to the local diary.
 *
 * Edits are limited to the entity registry, its avatar and the manual map
 * layout. Records, versions and media stay read-only here: the panel is for
 * arranging the map and fixing names, not for rewriting history.
 */
class DevMutations(private val db: RoomDatabase) {

    fun updateEntity(id: String, body: String): DevResponse {
        val payload = parse(body) ?: return DevResponse(400, """{"error":"invalid json"}""")
        val exists = db.rows("SELECT id FROM diary_entities WHERE id = ?", listOf(id)) { "1" }.isNotEmpty()
        if (!exists) return DevResponse(404, """{"error":"unknown entity"}""")
        db.openHelper.writableDatabase.execSQL(
            """
            UPDATE diary_entities SET
                name = COALESCE(?, name),
                avatarModel = COALESCE(?, avatarModel),
                avatarBackground = COALESCE(?, avatarBackground),
                skinColor = COALESCE(?, skinColor),
                hairColor = COALESCE(?, hairColor),
                clothingColor = COALESCE(?, clothingColor),
                updatedAt = ?
            WHERE id = ?
            """.trimIndent(),
            arrayOf(
                payload.string("name"),
                payload.string("model"),
                payload.number("background"),
                payload.number("skin"),
                payload.number("hair"),
                payload.number("clothing"),
                System.currentTimeMillis(),
                id,
            ),
        )
        return DevResponse(200, """{"ok":true}""")
    }

    fun pin(body: String): DevResponse {
        val payload = parse(body) ?: return DevResponse(400, """{"error":"invalid json"}""")
        val entityId = payload.string("entityId") ?: return DevResponse(400, """{"error":"entityId required"}""")
        val x = payload.number("x") ?: return DevResponse(400, """{"error":"x required"}""")
        val y = payload.number("y") ?: return DevResponse(400, """{"error":"y required"}""")
        db.openHelper.writableDatabase.execSQL(
            "INSERT OR REPLACE INTO map_pins (entityId, x, y) VALUES (?, ?, ?)",
            arrayOf(entityId, x.coerceIn(-1.6f, 1.6f), y.coerceIn(-1.6f, 1.6f)),
        )
        return DevResponse(200, """{"ok":true}""")
    }

    fun clearPins(): DevResponse {
        db.openHelper.writableDatabase.execSQL("DELETE FROM map_pins")
        return DevResponse(200, """{"ok":true}""")
    }

    private fun parse(body: String): JsonObject? =
        runCatching { Json.parseToJsonElement(body) as? JsonObject }.getOrNull()

    private fun JsonObject.string(name: String): String? =
        (get(name) as? JsonPrimitive)?.takeIf { it.isString }?.content

    private fun JsonObject.number(name: String): Float? =
        (get(name) as? JsonPrimitive)?.content?.toFloatOrNull()
}
