package com.callme.ai.features.conversations.adapters

import com.callme.ai.core.model.DatePrecision
import com.callme.ai.features.conversations.domain.Certainty
import com.callme.ai.features.conversations.domain.DiaryAction
import com.callme.ai.features.entities.domain.EntityType
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject

/**
 * Reads the diary actions from the validated `result` event.
 *
 * Every field is optional here because the action came from a language model:
 * anything unrecognised or incomplete is dropped instead of guessed, so a bad
 * action never reaches the local database.
 */
object DiaryActionParser {

    fun parse(result: JsonObject): List<DiaryAction> {
        val raw = result["actions"] ?: return emptyList()
        return runCatching { raw.jsonArray.toList() }.getOrNull().orEmpty().mapNotNull { element ->
            runCatching { element.jsonObject.toAction() }.getOrNull()
        }.take(MAX_ACTIONS)
    }

    private fun JsonObject.toAction(): DiaryAction? {
        val certainty = certainty("certainty")
        return when (string("kind")) {
            "create_entity" -> DiaryAction.CreateEntity(
                ref = string("ref") ?: return null,
                type = entityType(string("entity_kind")) ?: return null,
                name = string("name")?.takeIf { it.isNotBlank() } ?: return null,
                relation = string("relation").orEmpty(),
                certainty = certainty,
            )
            "create_event" -> event(certainty)
            "link_entity" -> link(certainty)
            "set_event_date" -> DiaryAction.SetEventDate(
                event = string("event") ?: return null,
                date = isoDate(string("event_date")) ?: return null,
                precision = precision(string("precision")),
                certainty = certainty,
            )
            else -> null
        }
    }

    private fun JsonObject.event(certainty: Certainty): DiaryAction? {
        val date = isoDate(string("event_date"))
        return DiaryAction.CreateEvent(
            ref = string("ref") ?: return null,
            title = string("title")?.takeIf { it.isNotBlank() } ?: return null,
            summary = string("summary").orEmpty(),
            date = date,
            precision = if (date == null) DatePrecision.UNKNOWN else precision(string("precision")),
            participants = strings("participants"),
            sourceIds = strings("source_ids"),
            certainty = certainty,
        )
    }

    private fun JsonObject.link(certainty: Certainty): DiaryAction? {
        val sourceId = string("source_id")
        val event = string("event")
        if (sourceId == null && event == null) return null
        return DiaryAction.LinkEntity(
            entity = string("entity") ?: return null,
            sourceId = sourceId,
            event = event,
            certainty = certainty,
        )
    }

    private fun JsonObject.string(name: String): String? =
        (this[name] as? JsonPrimitive)?.takeIf { it.isString }?.content

    private fun JsonObject.strings(name: String): List<String> =
        runCatching { this[name]?.jsonArray?.mapNotNull { (it as? JsonPrimitive)?.content } }
            .getOrNull().orEmpty()

    private fun JsonObject.certainty(name: String): Certainty =
        if (string(name) == "inferred") Certainty.INFERRED else Certainty.EXPLICIT

    private fun precision(value: String?): DatePrecision = when (value) {
        "day" -> DatePrecision.DAY
        "month" -> DatePrecision.MONTH
        "year" -> DatePrecision.YEAR
        else -> DatePrecision.UNKNOWN
    }

    private fun entityType(value: String?): EntityType? = when (value) {
        "person" -> EntityType.PERSON
        "animal" -> EntityType.ANIMAL
        "place" -> EntityType.PLACE
        else -> null
    }

    private fun isoDate(value: String?): String? =
        value?.takeIf { it.length >= 10 }?.take(10)?.takeIf {
            runCatching { java.time.LocalDate.parse(it) }.isSuccess
        }

    private const val MAX_ACTIONS = 12
}
