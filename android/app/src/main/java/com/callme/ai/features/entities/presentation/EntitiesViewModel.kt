package com.callme.ai.features.entities.presentation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.callme.ai.core.model.AvatarStyle
import com.callme.ai.core.model.Period
import com.callme.ai.features.entities.application.EntitiesRepository
import com.callme.ai.features.entities.domain.DiaryEntity
import com.callme.ai.features.entities.domain.EntityProfile
import com.callme.ai.features.entities.domain.EntityType
import java.time.YearMonth
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

/** Lists every registered entity and keeps edits on the same identity. */
class EntitiesViewModel(private val repository: EntitiesRepository) : ViewModel() {

    val entities: StateFlow<List<DiaryEntity>> = repository.observeEntities()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    fun create(type: EntityType, name: String, onCreated: (String) -> Unit) = viewModelScope.launch {
        if (name.isBlank()) return@launch
        onCreated(repository.create(type, name))
    }
}

/** Detail screen state for one entity, scoped to the visible period. */
class EntityDetailViewModel(
    private val repository: EntitiesRepository,
    private val entityId: String,
    month: String = "",
) : ViewModel() {

    /** Keeps the period the user was browsing in the connections area. */
    val period = MutableStateFlow(Period(month.takeIf { it.isNotBlank() }?.let(YearMonth::parse)))

    val profile: StateFlow<EntityProfile?> = period
        .flatMapLatest { repository.observeProfile(entityId, it) }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), null)

    fun setRelation(label: String) = viewModelScope.launch {
        repository.setRelationLabel(entityId, label)
    }

    fun rename(name: String) = viewModelScope.launch {
        if (name.isNotBlank()) repository.rename(entityId, name)
    }
}

/** Editor state for name and avatar of an existing entity. */
class AvatarEditorViewModel(
    private val repository: EntitiesRepository,
    private val entityId: String,
    initial: AvatarStyle?,
    initialName: String,
) : ViewModel() {

    val avatar = MutableStateFlow(initial ?: AvatarStyle("p1", 0xFFEAE5F6))
    val name = MutableStateFlow(initialName)

    fun onNameChange(value: String) { name.value = value }

    fun selectModel(model: String) = avatar.value.let { avatar.value = it.copy(model = model) }
    fun selectBackground(color: Long) = avatar.value.let { avatar.value = it.copy(background = color) }
    fun selectSkin(color: Long) = avatar.value.let { avatar.value = it.copy(skin = color) }
    fun selectHair(color: Long) = avatar.value.let { avatar.value = it.copy(hair = color) }
    fun selectClothing(color: Long) = avatar.value.let { avatar.value = it.copy(clothing = color) }

    fun save(onDone: () -> Unit) = viewModelScope.launch {
        repository.rename(entityId, name.value)
        repository.updateAvatar(entityId, avatar.value)
        onDone()
    }
}
