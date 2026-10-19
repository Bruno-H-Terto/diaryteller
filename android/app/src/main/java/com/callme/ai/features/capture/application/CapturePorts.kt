package com.callme.ai.features.capture.application

import com.callme.ai.features.capture.domain.DictationAvailability
import com.callme.ai.features.capture.domain.DictationEvent
import com.callme.ai.features.capture.domain.LocalRecording
import java.io.File
import kotlinx.coroutines.flow.Flow

/** Speech-to-text that never leaves the device. */
interface DictationEngine {
    fun availability(): DictationAvailability
    fun events(): Flow<DictationEvent>
    fun start(languageTag: String)
    fun stop()
    fun cancel()
    fun release()
}

/** Finished capture with its measured duration. */
data class CapturedAudio(val file: File, val durationMs: Long)

/** Microphone capture written straight to an app-private temporary file. */
interface AudioRecorder {
    fun start(): File
    fun stop(): CapturedAudio?
    fun cancel()
    val isRecording: Boolean
}

/** Encrypted local storage for voice notes. */
interface RecordingStore {
    fun save(temporaryFile: File, durationMs: Long): LocalRecording
    fun list(): List<LocalRecording>
    fun delete(id: String)
    /** Copies the decrypted audio to a private cache file for playback. */
    fun materialize(id: String): File?
}
