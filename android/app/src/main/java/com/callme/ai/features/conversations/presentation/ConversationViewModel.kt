package com.callme.ai.features.conversations.presentation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.callme.ai.features.conversations.application.ConversationRepository
import com.callme.ai.features.capture.application.DictationEngine
import com.callme.ai.features.conversations.application.DiaryMutator
import com.callme.ai.features.conversations.application.ReplySpeaker
import com.callme.ai.features.conversations.domain.ChatEvent
import com.callme.ai.features.conversations.domain.DiaryAction
import com.callme.ai.features.conversations.domain.ChatMessage
import com.callme.ai.features.records.application.RecordsRepository
import java.util.UUID
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class ConversationUiState(
    val messages: List<ChatMessage> = emptyList(),
    val streaming: Boolean = false,
    val error: String? = null,
    val voice: Boolean = false,
    val hearing: String = "",
    val selected: Set<String> = emptySet(),
)

class ConversationViewModel(
    private val repository: ConversationRepository,
    private val records: RecordsRepository,
    private val mutator: DiaryMutator,
    private val dictation: DictationEngine? = null,
    private val speaker: ReplySpeaker? = null,
) : ViewModel() {

    private val _state = MutableStateFlow(ConversationUiState())
    val state: StateFlow<ConversationUiState> = _state.asStateFlow()
    private var job: Job? = null
    private var pending: List<DiaryAction> = emptyList()
    private val narrations = mutableMapOf<String, String>()

    private val voice: ConversationVoice? = dictation?.let { engine ->
        ConversationVoice(
            engine = engine,
            scope = viewModelScope,
            languageTag = { java.util.Locale.getDefault().toLanguageTag() },
            onPartial = { text -> _state.value = _state.value.copy(hearing = text) },
            onUtterance = { text -> ask(text, _state.value.selected) },
            onUnavailable = {
                _state.value = _state.value.copy(voice = false, error = VOICE_UNAVAILABLE)
            },
        )
    }

    /** Turns the hands-free conversation on or off. */
    fun toggleVoice() {
        val manager = voice ?: return
        if (manager.listening) {
            manager.stop()
            _state.value = _state.value.copy(voice = false, hearing = "")
        } else {
            manager.start()
            _state.value = _state.value.copy(voice = true, error = null)
        }
    }

    fun toggleSelection(recordId: String) {
        val current = _state.value.selected
        _state.value = _state.value.copy(
            selected = if (recordId in current) current - recordId else current + recordId,
        )
    }

    fun ask(message: String, selected: Set<String>) {
        if (message.isBlank() || _state.value.streaming) return
        val answerId = UUID.randomUUID().toString()
        _state.value = _state.value.copy(
            messages = _state.value.messages +
                ChatMessage(UUID.randomUUID().toString(), true, message) +
                ChatMessage(answerId, false, ""),
            streaming = true,
            error = null,
        )
        pending = emptyList()
        job = viewModelScope.launch {
            runCatching {
                repository.ask(message, selected.toList(), selected.firstOrNull()).collect { event ->
                when (event) {
                    is ChatEvent.Started -> Unit
                    is ChatEvent.Delta -> append(answerId, event.text)
                    is ChatEvent.Proposed -> pending = event.actions
                    is ChatEvent.Failed -> _state.value = _state.value.copy(
                        streaming = false,
                        error = event.code,
                    )
                    is ChatEvent.Completed -> _state.value = _state.value.copy(streaming = false)
                    }
                }
            }.onFailure {
                _state.value = _state.value.copy(streaming = false, error = "unexpected")
            }
            if (_state.value.streaming) _state.value = _state.value.copy(streaming = false)
            attachProposals(answerId, message, pending)
            speakAnswer(answerId)
            // A failed turn must not restart the microphone in a loop.
            if (_state.value.error == null) voice?.resume()
        }
    }

    /** Reads the finished answer aloud only while the voice conversation is on. */
    private fun speakAnswer(answerId: String) {
        if (speaker == null || !_state.value.voice) return
        val answer = _state.value.messages.firstOrNull { it.id == answerId }?.text.orEmpty()
        if (answer.isNotBlank()) speaker.speak(answer)
    }

    /** Keeps model output visible but inert until the user confirms it. */
    private fun attachProposals(
        answerId: String,
        narration: String,
        actions: List<DiaryAction>,
    ) {
        if (actions.isEmpty()) return
        narrations[answerId] = narration.trim()
        _state.value = _state.value.copy(
            messages = _state.value.messages.map { message ->
                if (message.id == answerId) message.copy(proposals = actions) else message
            },
        )
    }

    /** Applies one reviewed turn locally and leaves an auditable change summary. */
    fun confirm(answerId: String) = viewModelScope.launch {
        val message = _state.value.messages.firstOrNull { it.id == answerId } ?: return@launch
        if (message.proposals.isEmpty()) return@launch
        val narration = narrations.remove(answerId).orEmpty()
        val recordId = narration.takeIf { it.isNotBlank() }
            ?.let { runCatching { records.createRecord(it) }.getOrNull() }
        val changes = runCatching { mutator.apply(message.proposals, recordId) }.getOrElse { emptyList() }
        _state.value = _state.value.copy(
            messages = _state.value.messages.map {
                if (it.id == answerId) it.copy(proposals = emptyList(), changes = changes) else it
            },
        )
    }

    /** Discards suggestions without writing a record, profile, link or event. */
    fun discard(answerId: String) {
        narrations.remove(answerId)
        _state.value = _state.value.copy(
            messages = _state.value.messages.map {
                if (it.id == answerId) it.copy(proposals = emptyList()) else it
            },
        )
    }

    fun cancel() {
        job?.cancel()
        _state.value = _state.value.copy(streaming = false)
    }

    override fun onCleared() {
        voice?.stop()
        speaker?.release()
    }

    private fun append(id: String, delta: String) {
        _state.value = _state.value.copy(
            messages = _state.value.messages.map { message ->
                if (message.id == id) message.copy(text = message.text + delta) else message
            },
        )
    }
}
