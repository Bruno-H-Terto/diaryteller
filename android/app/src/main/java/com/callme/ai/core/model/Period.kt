package com.callme.ai.core.model

import java.time.LocalDate
import java.time.YearMonth
import java.time.format.DateTimeFormatter
import java.util.Locale

private val ptBr: Locale = Locale.forLanguageTag("pt-BR")

/** Closed date range shown in the connections area; `null` means all history. */
data class Period(val month: YearMonth?) {

    val start: LocalDate get() = month?.atDay(1) ?: LocalDate.MIN
    val end: LocalDate get() = month?.atEndOfMonth() ?: LocalDate.MAX

    /** Inclusive range limited to two years back when the whole history is shown. */
    val queryStart: LocalDate get() = month?.atDay(1) ?: LocalDate.of(1970, 1, 1)
    val queryEnd: LocalDate get() = month?.atEndOfMonth() ?: LocalDate.of(2999, 12, 31)

    val label: String
        get() = month?.format(DateTimeFormatter.ofPattern("MMMM 'de' yyyy", ptBr))
            ?.replaceFirstChar { it.titlecase(ptBr) } ?: "Todo o histórico"

    fun previous(): Period = Period((month ?: YearMonth.now()).minusMonths(1))
    fun next(): Period = Period((month ?: YearMonth.now()).plusMonths(1))
}

/** Key used to remember an expanded day across navigation. */
fun Period.keyOf(date: LocalDate?): String = date?.toString() ?: "sem-data"
