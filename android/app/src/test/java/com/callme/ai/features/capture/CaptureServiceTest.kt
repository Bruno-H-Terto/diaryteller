package com.callme.ai.features.capture

import com.callme.ai.features.capture.application.AudioRecorder
import com.callme.ai.features.capture.application.CaptureService
import com.callme.ai.features.capture.application.CapturedAudio
import com.callme.ai.features.capture.application.DictationEngine
import com.callme.ai.features.capture.application.RecordingStore
import com.callme.ai.features.capture.domain.DictationAvailability
import com.callme.ai.features.capture.domain.DictationEvent
import com.callme.ai.features.capture.domain.LocalRecording
import com.google.common.truth.Truth.assertThat
import java.io.File
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.test.runTest
import org.junit.Test

class CaptureServiceTest {

    private class FakeDictation(
        private val availability: DictationAvailability = DictationAvailability.AVAILABLE,
    ) : DictationEngine {
        val flow = MutableSharedFlow<DictationEvent>()
        var started = false
        override fun availability() = availability
        override fun events(): Flow<DictationEvent> = flow
        override fun start(languageTag: String) {
            started = true
        }
        override fun stop() = Unit
        override fun cancel() = Unit
        override fun release() = Unit
    }

    private class FakeRecorder(private val file: File) : AudioRecorder {
        var cancelled = false
        override fun start(): File = file
        override fun stop(): CapturedAudio = CapturedAudio(file, 1_500)
        override fun cancel() {
            cancelled = true
        }
        override val isRecording: Boolean = false
    }

    private class FakeStore : RecordingStore {
        val saved = mutableListOf<Pair<File, Long>>()
        val deleted = mutableListOf<String>()
        override fun save(temporaryFile: File, durationMs: Long): LocalRecording {
            saved += temporaryFile to durationMs
            return LocalRecording("id", 1, durationMs, 10, null)
        }
        override fun list(): List<LocalRecording> = emptyList()
        override fun delete(id: String) {
            deleted += id
        }
        override fun materialize(id: String): File? = null
    }

    @Test
    fun `stop recording hands the captured file and duration to the store`() {
        val file = File.createTempFile("capture", ".m4a")
        val store = FakeStore()
        val service = CaptureService(FakeDictation(), FakeRecorder(file), store)

        val saved = service.stopRecording()

        assertThat(saved?.durationMs).isEqualTo(1_500)
        assertThat(store.saved.single().first).isEqualTo(file)
        assertThat(store.saved.single().second).isEqualTo(1_500)
    }

    @Test
    fun `dictation exposes availability and forwards start`() {
        val dictation = FakeDictation(DictationAvailability.MISSING_MODEL)
        val service = CaptureService(dictation, FakeRecorder(File("x")), FakeStore())

        assertThat(service.dictationAvailability()).isEqualTo(DictationAvailability.MISSING_MODEL)
        service.startDictation("pt-BR")
        assertThat(dictation.started).isTrue()
    }

    @Test
    fun `discarding a recording never stores it`() {
        val store = FakeStore()
        val recorder = FakeRecorder(File("x"))
        val service = CaptureService(FakeDictation(), recorder, store)

        service.discardRecording()

        assertThat(recorder.cancelled).isTrue()
        assertThat(store.saved).isEmpty()
    }

    @Test
    fun `delete only touches local storage`() {
        val store = FakeStore()
        CaptureService(FakeDictation(), FakeRecorder(File("x")), store).deleteRecording("note-1")
        assertThat(store.deleted).containsExactly("note-1")
    }
}
