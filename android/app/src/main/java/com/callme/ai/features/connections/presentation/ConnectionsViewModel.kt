package com.callme.ai.features.connections.presentation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.callme.ai.core.model.Period
import com.callme.ai.features.connections.application.ConnectionsRepository
import com.callme.ai.features.connections.application.MapData
import com.callme.ai.features.connections.domain.ConnectionNode
import com.callme.ai.features.connections.domain.ReviewItem
import com.callme.ai.features.connections.domain.TimelineEvent
import com.callme.ai.features.connections.domain.TimelineMonth
import com.callme.ai.features.connections.domain.groupTimeline
import com.callme.ai.features.entities.application.EntitiesRepository
import com.callme.ai.features.entities.domain.EntityProfile
import com.callme.ai.features.entities.domain.EntityType
import java.time.YearMonth
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

enum class ConnectionsMode { MAP, TIMELINE }

data class ConnectionsUiState(
    val mode: ConnectionsMode = ConnectionsMode.MAP,
    val period: Period = Period(YearMonth.now()),
    val type: EntityType? = null,
    val query: String = "",
    val searching: Boolean = false,
    val map: MapData? = null,
    val timeline: List<TimelineEvent> = emptyList(),
    val months: List<TimelineMonth> = emptyList(),
    val review: List<ReviewItem> = emptyList(),
    val expandedDays: Set<String> = emptySet(),
    val selected: ConnectionNode? = null,
    val profile: EntityProfile? = null,
    val reviewing: Boolean = false,
    val expandedGroup: Boolean = false,
    val pageSize: Int = PAGE,
) {
    val canLoadMore: Boolean get() = timeline.size >= pageSize

    private companion object {
        const val PAGE = 30
    }
}

/**
 * Single state for both views: switching between map and timeline keeps the
 * period, filters and expanded days, as required by the concept.
 */
class ConnectionsViewModel(
    private val repository: ConnectionsRepository,
    private val entities: EntitiesRepository,
) : ViewModel() {

    private val _state = MutableStateFlow(ConnectionsUiState())
    val state: StateFlow<ConnectionsUiState> = _state.asStateFlow()

    private val filters = _state.map { Filters(it.period, it.type, it.query) }.distinctUntilChanged()

    init {
        viewModelScope.launch {
            filters.flatMapLatest { repository.observeMap(it.period, it.type, it.query) }
                .collect { data -> _state.update { it.copy(map = data) } }
        }
        viewModelScope.launch {
            _state.map { it.period to it.pageSize }.distinctUntilChanged()
                .flatMapLatest { (period, size) -> repository.observeTimeline(period, size) }
                .collect { events ->
                    _state.update { it.copy(timeline = events, months = groupTimeline(events)) }
                }
        }
        viewModelScope.launch {
            repository.observeReview().collect { items -> _state.update { it.copy(review = items) } }
        }
        viewModelScope.launch {
            combine(
                _state.map { it.selected?.id }.distinctUntilChanged(),
                _state.map { it.period }.distinctUntilChanged(),
            ) { id, period -> id to period }
                .flatMapLatest { (id, period) ->
                    if (id == null) flowOf(null) else entities.observeProfile(id, period)
                }
                .collect { profile -> _state.update { it.copy(profile = profile) } }
        }
    }

    fun setMode(mode: ConnectionsMode) = _state.update { it.copy(mode = mode) }

    fun toggleSearch() = _state.update {
        it.copy(searching = !it.searching, query = if (it.searching) "" else it.query)
    }

    fun setQuery(value: String) = _state.update { it.copy(query = value) }

    fun setType(type: EntityType?) = _state.update { it.copy(type = type) }

    fun previousPeriod() = _state.update { it.copy(period = it.period.previous()) }

    fun nextPeriod() = _state.update { it.copy(period = it.period.next()) }

    fun useWholeHistory() = _state.update {
        it.copy(period = Period(null))
    }

    fun useCurrentMonth() = _state.update { it.copy(period = Period(YearMonth.now())) }

    fun select(node: ConnectionNode?) = _state.update { it.copy(selected = node) }

    fun openGroup() = _state.update { it.copy(expandedGroup = true) }

    fun closeGroup() = _state.update { it.copy(expandedGroup = false) }

    fun openReview() = _state.update { it.copy(reviewing = true) }

    fun closeReview() = _state.update { it.copy(reviewing = false) }

    fun toggleDay(key: String) = _state.update {
        val expanded = if (key in it.expandedDays) it.expandedDays - key else it.expandedDays + key
        it.copy(expandedDays = expanded)
    }

    fun loadMore() = _state.update { it.copy(pageSize = it.pageSize + 30) }

    fun confirm(item: ReviewItem) = viewModelScope.launch {
        repository.confirm(item)
    }

    fun discard(item: ReviewItem) = viewModelScope.launch {
        repository.discard(item)
    }

    private data class Filters(val period: Period, val type: EntityType?, val query: String)
}
