package com.callme.ai.features.records.presentation

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.callme.ai.core.model.DatePrecision
import com.callme.ai.core.model.eventDateValue
import com.callme.ai.features.records.application.RecordsRepository
import com.callme.ai.features.records.domain.Record
import com.callme.ai.features.records.domain.RecordVersion
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

class EditorViewModel(
    private val repository: RecordsRepository,
    private val recordId: String,
) : ViewModel() {

    val versions: StateFlow<List<RecordVersion>> = repository.observeVersions(recordId)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    val record: StateFlow<Record?> = repository.observeRecord(recordId)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), null)

    var text by mutableStateOf("")
        private set

    init {
        viewModelScope.launch {
            text = repository.observeVersions(recordId).first().lastOrNull()?.content.orEmpty()
        }
    }

    /** Appends a locally produced transcript to the entry being written. */
    fun applyTranscript(value: String) {
        if (value.isBlank()) return
        text = listOf(text.trim(), value.trim()).filter { it.isNotBlank() }.joinToString("\n\n")
    }

    fun onTextChange(value: String) {
        text = value
        viewModelScope.launch { repository.updateDraft(recordId, value) }
    }

    fun save(onSaved: () -> Unit) = viewModelScope.launch {
        val current = repository.observeVersions(recordId).first().lastOrNull()
        if (current?.confirmed == false) {
            repository.confirmDraft(recordId, text)
        } else if (current != null && current.content != text) {
            repository.addVersion(recordId, text)
        }
        onSaved()
    }

    /** Stores the narrated date with the precision the user confirmed. */
    fun setEventDate(year: Int, month: Int?, day: Int?, precision: DatePrecision) = viewModelScope.launch {
        repository.setEventDate(recordId, eventDateValue(year, month, day, precision), precision)
    }

    fun clearEventDate() = viewModelScope.launch {
        repository.setEventDate(recordId, null, DatePrecision.UNKNOWN)
    }

    fun restore(versionId: String) = viewModelScope.launch {
        repository.restoreVersion(recordId, versionId)
        text = repository.observeVersions(recordId).first().last().content
    }
}
