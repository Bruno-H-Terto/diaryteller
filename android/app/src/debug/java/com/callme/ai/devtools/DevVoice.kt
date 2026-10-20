package com.callme.ai.devtools

import android.content.Context
import com.callme.ai.bootstrap.CallMeApplication
import java.io.File
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

/**
 * Voice rehearsal routes for the studio panel.
 *
 * The emulator has no microphone, so the audio loop is exercised with a WAV the
 * panel pushes into the app: one route transcribes it, the other makes the
 * microphone button replay it through the same recogniser.
 */
object DevVoice {

    private var context: Context? = null

    fun attach(application: CallMeApplication) {
        context = application
    }

    fun application(): CallMeApplication = context as? CallMeApplication
        ?: error("app not ready")

    fun replay(body: String): DevResponse {
        val file = path(body) ?: return DevResponse(400, """{"error":"path required"}""")
        val application = context as? CallMeApplication
            ?: return DevResponse(503, """{"error":"app not ready"}""")
        DevTools.setReplay(file)
        application.container.dictation = ReplayDictation(application, application.container.speechModel)
        return DevResponse(200, """{"ok":true,"file":${quote(file)}}""")
    }

    /** Synthesises the phrase with the device voice so it can be replayed. */
    fun say(body: String): DevResponse {
        val request = runCatching {
            Json.parseToJsonElement(body).jsonObject
        }.getOrNull() ?: return DevResponse(400, """{"error":"invalid json"}""")
        val text = request["text"]?.jsonPrimitive?.content
            ?: return DevResponse(400, """{"error":"text required"}""")
        val language = request["language"]?.jsonPrimitive?.content ?: "pt-BR"
        val application = context as? CallMeApplication
            ?: return DevResponse(503, """{"error":"app not ready"}""")
        val file = DevSpeech.say(application, text, language)
            ?: return DevResponse(422, """{"error":${quote("voice unavailable for $language")}}""")
        return DevResponse(200, """{"ok":true,"file":${quote(file.name)}}""")
    }

    fun transcribe(body: String): DevResponse {
        val file = path(body) ?: return DevResponse(400, """{"error":"path required"}""")
        val application = context as? CallMeApplication
            ?: return DevResponse(503, """{"error":"app not ready"}""")
        val target = File(application.filesDir, file)
        val text = runBlocking { application.container.fileTranscriber.transcribe(target) }
            ?: return failed(application.container.speechModel.failure())
        return DevResponse(200, """{"text":${quote(text)}}""")
    }

    private fun failed(model: String?): DevResponse =
        DevResponse(422, """{"error":"transcription failed","model":${quote(model ?: "loaded")}}""")

    private fun path(body: String): String? = runCatching {
        Json.parseToJsonElement(body).jsonObject["path"]?.jsonPrimitive?.content
    }.getOrNull()
}
