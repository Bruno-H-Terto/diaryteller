package com.callme.ai.features.connections.presentation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.callme.ai.core.model.DatePrecision
import com.callme.ai.core.model.eventDateValue
import com.callme.ai.features.connections.application.ConnectionsRepository
import com.callme.ai.features.connections.domain.TimelineEvent
import java.time.LocalDate
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

/** State of one event: its sources, people and the explicit date precision. */
class EventViewModel(
    private val repository: ConnectionsRepository,
    private val eventId: String,
) : ViewModel() {

    val event: StateFlow<TimelineEvent?> = repository.observeEvent(eventId)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), null)

    fun setDate(year: Int, month: Int?, day: Int?, precision: DatePrecision) {
        val iso = eventDateValue(year, month, day, precision)
        viewModelScope.launch { repository.setEventDate(eventId, iso, precision) }
    }

    fun clearDate() = viewModelScope.launch {
        repository.setEventDate(eventId, null, DatePrecision.UNKNOWN)
    }

    fun detach(recordId: String) = viewModelScope.launch {
        repository.detachSource(eventId, recordId)
    }

    /** Year shown as the starting point of the correction dialog. */
    fun suggestedYear(): Int = event.value?.date?.year ?: LocalDate.now().year
}
