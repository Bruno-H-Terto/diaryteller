package com.callme.ai.core.model

import com.google.common.truth.Truth.assertThat
import org.junit.Test

class EventDateTest {

    @Test
    fun `year precision never invents a month or a day`() {
        val stored = eventDateValue(2019, month = null, day = null, DatePrecision.YEAR)

        assertThat(stored).isEqualTo("2019-01-01")
        assertThat(eventDateLabel(parseEventDate(stored), DatePrecision.YEAR)).isEqualTo("2019")
        assertThat(eventDateNote(DatePrecision.YEAR, suggested = false)).contains("mês e dia não informados")
    }

    @Test
    fun `month precision ignores a missing day`() {
        val stored = eventDateValue(2026, month = 10, day = null, DatePrecision.MONTH)

        assertThat(stored).isEqualTo("2026-10-01")
        assertThat(eventDateLabel(parseEventDate(stored), DatePrecision.MONTH)).isEqualTo("Outubro de 2026")
    }

    @Test
    fun `unknown precision stores nothing`() {
        assertThat(eventDateValue(2026, 10, 19, DatePrecision.UNKNOWN)).isNull()
        assertThat(eventDateLabel(null, DatePrecision.UNKNOWN)).isEqualTo("Sem data definida")
    }

    @Test
    fun `day precision keeps the full date`() {
        val stored = eventDateValue(2026, 10, 19, DatePrecision.DAY)

        assertThat(stored).isEqualTo("2026-10-19")
        assertThat(eventDateLabel(parseEventDate(stored), DatePrecision.DAY)).isEqualTo("19 de out 2026")
    }

    @Test
    fun `suggested dates are shown as needing review`() {
        assertThat(eventDateNote(DatePrecision.DAY, suggested = true)).contains("a revisar")
    }
}
