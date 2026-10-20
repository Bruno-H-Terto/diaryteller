package com.callme.ai.devtools

import com.callme.ai.bootstrap.CallMeApplication
import java.io.File
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

/**
 * Rehearsal helper: attaches a pushed audio file to an entry as if it had been
 * recorded in the app, so the editor path can be exercised where there is no
 * microphone. Debug builds only.
 */
object DevRecords {

    fun attachAudio(application: CallMeApplication, body: String): DevResponse {
        val request = runCatching { Json.parseToJsonElement(body).jsonObject }.getOrNull()
            ?: return DevResponse(400, """{"error":"invalid json"}""")
        val recordId = request["recordId"]?.jsonPrimitive?.content
            ?: return DevResponse(400, """{"error":"recordId required"}""")
        val name = request["path"]?.jsonPrimitive?.content
            ?: return DevResponse(400, """{"error":"path required"}""")
        val source = File(application.filesDir, name)
        if (!source.exists()) return DevResponse(404, """{"error":"file not found"}""")
        val media = application.container.media
        val stored = runBlocking { media.saveRecording(source, durationMs(source)) }
        runBlocking { media.attachAudio(recordId, stored.id) }
        return DevResponse(200, """{"ok":true,"recordingId":${quote(stored.id)}}""")
    }

    private fun durationMs(file: File): Long = 3_000L
}
