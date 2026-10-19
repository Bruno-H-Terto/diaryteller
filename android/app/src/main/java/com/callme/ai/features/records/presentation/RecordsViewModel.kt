package com.callme.ai.features.records.presentation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.callme.ai.features.records.application.RecordsRepository
import com.callme.ai.features.records.domain.Record
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

class RecordsViewModel(private val repository: RecordsRepository) : ViewModel() {

    val records: StateFlow<List<Record>> = repository.observeRecords()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    fun createDraft(onCreated: (String) -> Unit) = viewModelScope.launch {
        onCreated(repository.createDraft())
    }

    fun delete(recordId: String) = viewModelScope.launch { repository.deleteRecord(recordId) }
}
