package com.callme.ai.features.entities.presentation

import androidx.compose.runtime.Composable
import androidx.compose.ui.res.stringResource
import com.callme.ai.R
import com.callme.ai.features.entities.domain.EntityType

/** Entity types offered as filters; self is never a filter. */
enum class EntityFilters(val type: EntityType, private val labelRes: Int) {
    PEOPLE(EntityType.PERSON, R.string.filter_people),
    ANIMALS(EntityType.ANIMAL, R.string.filter_animals),
    PLACES(EntityType.PLACE, R.string.filter_places),
    EVENTS(EntityType.EVENT, R.string.filter_events),
    ;

    @Composable
    fun label(): String = stringResource(labelRes)
}
