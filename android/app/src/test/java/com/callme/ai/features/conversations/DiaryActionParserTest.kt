package com.callme.ai.features.conversations

import com.callme.ai.core.model.DatePrecision
import com.callme.ai.features.conversations.adapters.DiaryActionParser
import com.callme.ai.features.conversations.domain.Certainty
import com.callme.ai.features.conversations.domain.DiaryAction
import com.callme.ai.features.entities.domain.EntityType
import com.google.common.truth.Truth.assertThat
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import org.junit.Test

class DiaryActionParserTest {

    private fun parse(json: String) = DiaryActionParser.parse(Json.parseToJsonElement(json).jsonObject)

    @Test
    fun `reads an entity, an event and a link`() {
        val actions = parse(
            """
            {"actions":[
              {"kind":"create_entity","ref":"new:1","entity_kind":"person","name":"Carlos","relation":"colega"},
              {"kind":"create_event","ref":"new:2","title":"Mercado","event_date":"2026-10-19",
               "precision":"day","participants":["new:1","a1"],"certainty":"inferred"},
              {"kind":"link_entity","entity":"new:1","source_id":"r1"}
            ]}
            """.trimIndent(),
        )
        assertThat(actions).hasSize(3)
        val entity = actions[0] as DiaryAction.CreateEntity
        assertThat(entity.name).isEqualTo("Carlos")
        assertThat(entity.type).isEqualTo(EntityType.PERSON)
        val event = actions[1] as DiaryAction.CreateEvent
        assertThat(event.date).isEqualTo("2026-10-19")
        assertThat(event.precision).isEqualTo(DatePrecision.DAY)
        assertThat(event.participants).containsExactly("new:1", "a1")
        assertThat(event.certainty).isEqualTo(Certainty.INFERRED)
    }

    @Test
    fun `drops actions without the fields needed to write them`() {
        val actions = parse(
            """
            {"actions":[
              {"kind":"create_entity","ref":"new:1","entity_kind":"ghost","name":"X"},
              {"kind":"create_event","ref":"new:2"},
              {"kind":"link_entity","entity":"a1"},
              {"kind":"move_map","ref":"new:3"}
            ]}
            """.trimIndent(),
        )
        assertThat(actions).isEmpty()
    }

    @Test
    fun `undated event keeps unknown precision`() {
        val actions = parse(
            """{"actions":[{"kind":"create_event","ref":"new:1","title":"Sem data","precision":"day"}]}""",
        )
        val event = actions.single() as DiaryAction.CreateEvent
        assertThat(event.date).isNull()
        assertThat(event.precision).isEqualTo(DatePrecision.UNKNOWN)
    }

    @Test
    fun `result without actions yields an empty list`() {
        assertThat(parse("""{"source_ids":[]}""")).isEmpty()
    }
}
