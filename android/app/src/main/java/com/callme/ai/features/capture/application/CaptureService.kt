package com.callme.ai.features.capture.application

import com.callme.ai.features.capture.domain.DictationAvailability
import com.callme.ai.features.capture.domain.DictationEvent
import com.callme.ai.features.capture.domain.LocalRecording
import kotlinx.coroutines.flow.Flow
import java.io.File

/** Use case layer for voice capture; orchestration only, no Android APIs. */
class CaptureService(
    private val dictation: DictationEngine,
    private val recorder: AudioRecorder,
    private val recordings: RecordingStore,
) {
    fun dictationAvailability(): DictationAvailability = dictation.availability()

    fun dictationEvents(): Flow<DictationEvent> = dictation.events()

    fun startDictation(languageTag: String) = dictation.start(languageTag)

    fun stopDictation() = dictation.stop()

    fun cancelDictation() = dictation.cancel()

    fun startRecording(): File = recorder.start()

    fun stopRecording(): LocalRecording? {
        val captured = recorder.stop() ?: return null
        return recordings.save(captured.file, captured.durationMs)
    }

    fun discardRecording() {
        recorder.cancel()
    }

    fun recording(id: String): File? = recordings.materialize(id)

    fun localRecordings(): List<LocalRecording> = recordings.list()

    fun deleteRecording(id: String) = recordings.delete(id)
}
