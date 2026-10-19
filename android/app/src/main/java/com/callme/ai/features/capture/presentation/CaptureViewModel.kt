package com.callme.ai.features.capture.presentation

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.callme.ai.features.capture.application.CaptureService
import com.callme.ai.features.capture.domain.DictationAvailability
import com.callme.ai.features.capture.domain.DictationEvent
import com.callme.ai.features.capture.domain.DictationFailure
import com.callme.ai.features.capture.domain.LocalRecording
import com.callme.ai.features.records.application.RecordsRepository
import kotlinx.coroutines.launch

enum class CapturePhase { IDLE, LISTENING, RECORDING, REVIEW, SAVING }

class CaptureViewModel(
    private val service: CaptureService,
    private val records: RecordsRepository,
) : ViewModel() {

    var phase by mutableStateOf(CapturePhase.IDLE)
        private set
    var transcript by mutableStateOf("")
        private set
    var error by mutableStateOf<DictationFailure?>(null)
        private set
    var recordings by mutableStateOf<List<LocalRecording>>(emptyList())
        private set
    var elapsedMs by mutableStateOf(0L)
        private set
    var playingId by mutableStateOf<String?>(null)
        private set

    val availability: DictationAvailability = service.dictationAvailability()

    init {
        viewModelScope.launch {
            service.dictationEvents().collect { event ->
                when (event) {
                    is DictationEvent.Ready -> phase = CapturePhase.LISTENING
                    is DictationEvent.Partial -> transcript = event.text
                    is DictationEvent.Final -> {
                        transcript = event.text
                        phase = CapturePhase.REVIEW
                    }
                    is DictationEvent.Failed -> {
                        error = event.reason
                        phase = if (transcript.isBlank()) CapturePhase.IDLE else CapturePhase.REVIEW
                        service.cancelDictation()
                    }
                }
            }
        }
        refresh()
    }

    fun startDictation(languageTag: String) {
        error = null
        if (availability != DictationAvailability.AVAILABLE) return
        transcript = ""
        phase = CapturePhase.LISTENING
        service.startDictation(languageTag)
    }

    fun stopDictation() = service.stopDictation()

    fun cancelDictation() {
        service.cancelDictation()
        transcript = ""
        phase = CapturePhase.IDLE
    }

    override fun onCleared() {
        service.cancelDictation()
        service.discardRecording()
    }

    fun startRecording() {
        error = null
        service.startRecording()
        phase = CapturePhase.RECORDING
    }

    fun stopRecording() {
        val saved = service.stopRecording()
        refresh()
        phase = CapturePhase.IDLE
        playingId = saved?.id
        elapsedMs = saved?.durationMs ?: 0L
    }

    fun discardRecording() {
        service.discardRecording()
        phase = CapturePhase.IDLE
    }

    fun play(recording: LocalRecording, onFile: (java.io.File) -> Unit) {
        playingId = recording.id
        service.recording(recording.id)?.let(onFile)
    }

    fun delete(recording: LocalRecording) {
        service.deleteRecording(recording.id)
        refresh()
    }

    fun saveTranscript(onSaved: (String) -> Unit) {
        if (transcript.isBlank()) return
        phase = CapturePhase.SAVING
        viewModelScope.launch {
            val recordId = records.createRecord(transcript.trim())
            phase = CapturePhase.IDLE
            onSaved(recordId)
        }
    }

    private fun refresh() {
        viewModelScope.launch { recordings = service.localRecordings() }
    }
}
