package com.callme.ai.features.capture.adapters

import android.annotation.SuppressLint
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import com.callme.ai.features.capture.application.DictationEngine
import com.callme.ai.features.capture.domain.DictationAvailability
import com.callme.ai.features.capture.domain.DictationEvent
import com.callme.ai.features.capture.domain.DictationFailure
import java.util.concurrent.atomic.AtomicBoolean
import kotlin.concurrent.thread
import kotlinx.coroutines.channels.BufferOverflow
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import org.vosk.Recognizer

/**
 * Speech recognition with the model bundled in the app.
 *
 * Audio is read from the microphone into a [Recognizer] on a worker thread and
 * never leaves the device. Partial results are emitted while the user speaks;
 * stopping the loop finalises the last phrase.
 */
class VoskDictation(
    private val model: VoskModel,
    private val sampleRate: Int = SAMPLE_RATE,
) : DictationEngine {

    private val _events = MutableSharedFlow<DictationEvent>(
        replay = 0,
        extraBufferCapacity = 32,
        onBufferOverflow = BufferOverflow.DROP_OLDEST,
    )
    override fun events(): Flow<DictationEvent> = _events.asSharedFlow()

    private val running = AtomicBoolean(false)
    private var worker: Thread? = null

    override fun availability(): DictationAvailability {
        if (!model.available()) return DictationAvailability.MISSING_MODEL
        return DictationAvailability.AVAILABLE
    }

    @SuppressLint("MissingPermission")
    override fun start(languageTag: String) {
        if (running.getAndSet(true)) return
        val loaded = model.await() ?: run {
            running.set(false)
            fail(DictationFailure.OFFLINE_PACK_MISSING)
            return
        }
        _events.tryEmit(DictationEvent.Ready)
        worker = thread(name = "vosk-dictation", isDaemon = true) {
            listen(loaded)
        }
    }

    private fun listen(loaded: org.vosk.Model) {
        val minimum = AudioRecord.getMinBufferSize(sampleRate, CHANNEL, ENCODING)
        if (minimum <= 0) {
            running.set(false)
            fail(DictationFailure.AUDIO_ERROR)
            return
        }
        val recorder = createRecorder(minimum)
        if (recorder == null) {
            running.set(false)
            fail(DictationFailure.PERMISSION_DENIED)
            return
        }
        val recognizer = runCatching { Recognizer(loaded, sampleRate.toFloat()) }.getOrNull()
        if (recognizer == null) {
            recorder.release()
            running.set(false)
            fail(DictationFailure.CLIENT_ERROR)
            return
        }
        val buffer = ByteArray(BUFFER_BYTES)
        try {
            recorder.startRecording()
            while (running.get()) {
                val read = recorder.read(buffer, 0, buffer.size)
                if (read <= 0) continue
                if (recognizer.acceptWaveForm(buffer, read)) {
                    emitText(recognizer.result, final = false)
                } else {
                    emitText(recognizer.partialResult, final = false, partial = true)
                }
            }
            emitText(recognizer.finalResult, final = true)
        } finally {
            runCatching { recorder.stop() }
            recorder.release()
            recognizer.close()
        }
    }

    @SuppressLint("MissingPermission")
    private fun createRecorder(minimum: Int): AudioRecord? = runCatching {
        AudioRecord(
            MediaRecorder.AudioSource.VOICE_RECOGNITION,
            sampleRate,
            CHANNEL,
            ENCODING,
            minimum * 4,
        ).takeIf { it.state == AudioRecord.STATE_INITIALIZED }
    }.getOrNull()

    override fun stop() {
        if (!running.getAndSet(false)) return
        worker?.join(FINALIZE_TIMEOUT_MS)
        worker = null
    }

    override fun cancel() {
        running.set(false)
        worker?.join(FINALIZE_TIMEOUT_MS)
        worker = null
    }

    override fun release() = cancel()

    private fun emitText(json: String, final: Boolean, partial: Boolean = false) {
        val text = textOf(json)
        if (text.isBlank()) return
        _events.tryEmit(
            if (final) DictationEvent.Final(text) else DictationEvent.Partial(text),
        )
        if (partial) return
    }

    private fun fail(reason: DictationFailure) {
        _events.tryEmit(DictationEvent.Failed(reason))
    }

    /** Vosk answers `{"text": "..."}` or `{"partial": "..."}`. */
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
        const val CHANNEL = AudioFormat.CHANNEL_IN_MONO
        const val ENCODING = AudioFormat.ENCODING_PCM_16BIT
        const val BUFFER_BYTES = 4_096
        const val FINALIZE_TIMEOUT_MS = 2_500L
    }
}
