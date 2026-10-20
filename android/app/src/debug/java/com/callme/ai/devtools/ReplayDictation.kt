package com.callme.ai.devtools

import android.content.Context
import com.callme.ai.features.capture.adapters.VoskModel
import com.callme.ai.features.capture.application.DictationEngine
import com.callme.ai.features.capture.domain.DictationAvailability
import com.callme.ai.features.capture.domain.DictationEvent
import com.callme.ai.features.capture.domain.DictationFailure
import java.io.File
import kotlin.concurrent.thread
import kotlinx.coroutines.channels.BufferOverflow
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import org.vosk.Recognizer

/**
 * Feeds a WAV file to the same on-device recogniser the microphone uses.
 *
 * The emulator has no microphone, so rehearsing the voice loop there would be
 * impossible. This engine lets the studio replay a recording through Vosk and
 * emit the same partial and final events, keeping the app path untouched.
 */
class ReplayDictation(
    private val context: Context,
    private val model: VoskModel,
) : DictationEngine {

    private val _events = MutableSharedFlow<DictationEvent>(
        replay = 0,
        extraBufferCapacity = 32,
        onBufferOverflow = BufferOverflow.DROP_OLDEST,
    )
    override fun events(): Flow<DictationEvent> = _events.asSharedFlow()

    @Volatile
    private var playing = false

    override fun availability(): DictationAvailability = DictationAvailability.AVAILABLE

    override fun start(languageTag: String) {
        val file = DevTools.replayFile() ?: run {
            fail(DictationFailure.CLIENT_ERROR)
            return
        }
        val loaded = model.await() ?: run {
            fail(DictationFailure.OFFLINE_PACK_MISSING)
            return
        }
        playing = true
        _events.tryEmit(DictationEvent.Ready)
        thread(name = "replay-dictation", isDaemon = true) {
            val recognizer = runCatching { Recognizer(loaded, SAMPLE_RATE.toFloat()) }.getOrNull()
                ?: return@thread fail(DictationFailure.CLIENT_ERROR)
            try {
                read(File(context.filesDir, file)) { chunk, length ->
                    if (!playing) return@read false
                    if (recognizer.acceptWaveForm(chunk, length)) {
                        emit(textOf(recognizer.result))
                    }
                    // Pace the file like real speech so the UI shows progress.
                    Thread.sleep(STEP_MS)
                    true
                }
                emit(textOf(recognizer.finalResult), final = true)
            } finally {
                recognizer.close()
                playing = false
            }
        }
    }

    override fun stop() {
        playing = false
    }

    override fun cancel() {
        playing = false
    }

    override fun release() = cancel()

    private inline fun read(file: File, onChunk: (ByteArray, Int) -> Boolean) {
        if (!file.exists()) return
        file.inputStream().use { stream ->
            stream.skip(HEADER)
            val buffer = ByteArray(CHUNK)
            while (true) {
                val length = stream.read(buffer)
                if (length <= 0) break
                if (!onChunk(buffer, length)) break
            }
        }
    }

    private fun emit(text: String, final: Boolean = false) {
        if (text.isBlank()) return
        _events.tryEmit(if (final) DictationEvent.Final(text) else DictationEvent.Partial(text))
    }

    private fun fail(reason: DictationFailure) {
        _events.tryEmit(DictationEvent.Failed(reason))
    }

    private fun textOf(json: String): String {
        val key = if (json.contains("\"partial\"")) "\"partial\"" else "\"text\""
        val start = json.indexOf(key)
        if (start < 0) return ""
        val open = json.indexOf('"', start + key.length + 1)
        val close = json.lastIndexOf('"')
        return if (open in 0 until close) json.substring(open + 1, close).trim() else ""
    }

    private companion object {
        const val SAMPLE_RATE = 16_000
        const val CHUNK = 8_192
        const val HEADER = 44L
        const val STEP_MS = 250L
    }
}
