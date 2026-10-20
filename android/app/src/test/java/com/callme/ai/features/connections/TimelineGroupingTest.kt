package com.callme.ai.features.connections

import com.callme.ai.core.model.AvatarStyle
import com.callme.ai.core.model.DatePrecision
import com.callme.ai.features.connections.domain.TimelineEvent
import com.callme.ai.features.connections.domain.UNDATED_KEY
import com.callme.ai.features.connections.domain.groupTimeline
import com.callme.ai.features.entities.domain.RelationOrigin
import com.google.common.truth.Truth.assertThat
import java.time.LocalDate
import org.junit.Test

class TimelineGroupingTest {

    private fun event(id: String, date: String?, precision: DatePrecision = DatePrecision.DAY) = TimelineEvent(
        id = id,
        title = id,
        summary = "",
        date = date?.let(LocalDate::parse),
        precision = precision,
        coverUri = null,
        origin = RelationOrigin.DECLARED,
        suggested = false,
        participants = emptyList(),
        place = null,
        sources = emptyList(),
    )

    @Test
    fun `months and days are ordered from newest to oldest`() {
        val months = groupTimeline(
            listOf(
                event("aug", "2026-08-04"),
                event("oct-late", "2026-10-19"),
                event("oct-early", "2026-10-03"),
            ),
        )

        assertThat(months.map { it.key }).containsExactly("2026-10", "2026-08").inOrder()
        assertThat(months.first().days.map { it.key }).containsExactly("2026-10-19", "2026-10-03").inOrder()
    }

    @Test
    fun `undated events go to a separate trailing bucket`() {
        val months = groupTimeline(
            listOf(
                event("unknown", null, DatePrecision.UNKNOWN),
                event("day", "2026-10-19"),
            ),
        )

        assertThat(months.map { it.key }).containsExactly("2026-10", UNDATED_KEY).inOrder()
        assertThat(months.last().days.single().date).isNull()
        assertThat(months.last().days.single().events.single().id).isEqualTo("unknown")
    }

    @Test
    fun `a year-only event never invents a month or a day`() {
        val months = groupTimeline(
            listOf(event("mudanca", "2019-01-01", DatePrecision.YEAR)),
        )

        assertThat(months.single().label).isEqualTo("2019")
        assertThat(months.single().days.single().label).isEqualTo("2019 · ano informado")
        assertThat(months.single().days.single().events.single().precision).isEqualTo(DatePrecision.YEAR)
    }

    @Test
    fun `a month-only event is grouped without a fabricated day`() {
        val months = groupTimeline(
            listOf(event("mes", "2026-10-01", DatePrecision.MONTH)),
        )

        assertThat(months.single().days.single().label).isEqualTo("Outubro de 2026 · mês informado")
    }

    @Test
    fun `avatar style is carried through unchanged`() {
        val style = AvatarStyle("p2", 0xFFEAE5F6, 1L, 2L, 3L)
        assertThat(style.copy(background = style.background)).isEqualTo(style)
    }
}
