package com.callme.ai.features.settings.presentation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.callme.ai.core.database.SampleDiary
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

/** Installs or removes the synthetic diary used for local validation. */
class SampleDataViewModel(private val sample: SampleDiary) : ViewModel() {

    val installed: StateFlow<Boolean> = sample.observeInstalled()
        .map { it > 0 }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), false)

    fun toggle() = viewModelScope.launch {
        if (installed.value) sample.remove() else sample.insert()
    }
}
