package com.callme.ai.features.conversations.presentation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.callme.ai.features.conversations.application.ConversationRepository
import com.callme.ai.features.conversations.domain.ChatEvent
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
)

class ConversationViewModel(
    private val repository: ConversationRepository,
    private val records: RecordsRepository,
) : ViewModel() {

    private val _state = MutableStateFlow(ConversationUiState())
    val state: StateFlow<ConversationUiState> = _state.asStateFlow()
    private var job: Job? = null

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
        job = viewModelScope.launch {
            runCatching {
                repository.ask(message, selected.toList()).collect { event ->
                when (event) {
                    is ChatEvent.Started -> Unit
                    is ChatEvent.Delta -> append(answerId, event.text)
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
        }
    }

    fun cancel() {
        job?.cancel()
        _state.value = _state.value.copy(streaming = false)
    }

    private fun append(id: String, delta: String) {
        _state.value = _state.value.copy(
            messages = _state.value.messages.map { message ->
                if (message.id == id) message.copy(text = message.text + delta) else message
            },
        )
    }
}
