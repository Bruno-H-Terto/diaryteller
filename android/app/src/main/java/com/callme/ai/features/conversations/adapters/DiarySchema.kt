package com.callme.ai.features.conversations.adapters

import com.callme.ai.core.database.EntitiesDao
import com.callme.ai.core.model.DatePrecision
import com.callme.ai.features.conversations.domain.Certainty
import com.callme.ai.features.entities.domain.EntityType

/** How the local schema spells the values a conversation produces. */
internal class DiarySchema {

    /** Review state and origin derived from how certain the model was. */
    fun state(certainty: Certainty): AppliedState =
        if (certainty == Certainty.EXPLICIT) {
            AppliedState(CONFIRMED, DECLARED)
        } else {
            AppliedState(SUGGESTED, SUGGESTED)
        }

    fun entityType(value: String): EntityType =
        runCatching { EntityType.valueOf(value) }.getOrDefault(EntityType.PERSON)

    fun precision(value: String): DatePrecision =
        runCatching { DatePrecision.valueOf(value) }.getOrDefault(DatePrecision.UNKNOWN)

    fun model(type: EntityType): String = when (type) {
        EntityType.ANIMAL -> "a1"
        EntityType.PLACE -> "l1"
        EntityType.EVENT -> "e1"
        else -> "p1"
    }

    /** Role of one participant in an event: places are places, everyone else people. */
    suspend fun role(dao: EntitiesDao, entityId: String): String =
        if (dao.entity(entityId)?.type == EntityType.PLACE.name) PLACE else PERSON

    companion object {
        const val CONFIRMED = "CONFIRMED"
        const val SUGGESTED = "SUGGESTED"
        const val DECLARED = "DECLARED"
        const val PERSON = "PERSON"
        const val PLACE = "PLACE"
    }
}

/** The two strings one certainty maps to in the local schema. */
internal data class AppliedState(val review: String, val origin: String)
