package com.callme.ai.core.model

import java.time.LocalDate
import java.time.YearMonth
import java.time.format.DateTimeFormatter
import java.util.Locale

/**
 * How precisely a narrated date is known. The stored ISO value only carries the
 * parts the narrator actually gave, so a year never gains a month or day.
 */
enum class DatePrecision { DAY, MONTH, YEAR, UNKNOWN }

private val ptBr: Locale = Locale.forLanguageTag("pt-BR")

/** Builds the stored value from the parts the user confirmed. */
fun eventDateValue(year: Int, month: Int?, day: Int?, precision: DatePrecision): String? = when (precision) {
    DatePrecision.DAY -> month?.let { m -> day?.let { d -> LocalDate.of(year, m, d).toString() } }
    DatePrecision.MONTH -> month?.let { YearMonth.of(year, it).atDay(1).toString() }
    DatePrecision.YEAR -> LocalDate.of(year, 1, 1).toString()
    DatePrecision.UNKNOWN -> null
}

fun parseEventDate(value: String?): LocalDate? =
    value?.takeIf { it.length >= 10 }?.let { runCatching { LocalDate.parse(it.take(10)) }.getOrNull() }

/** Human label that states the known precision instead of guessing a date. */
fun eventDateLabel(date: LocalDate?, precision: DatePrecision): String = when (precision) {
    DatePrecision.DAY -> date?.format(DateTimeFormatter.ofPattern("d 'de' MMM yyyy", ptBr))
        ?.replace(".", "")
        .orEmpty()
    DatePrecision.MONTH -> date?.format(DateTimeFormatter.ofPattern("MMMM 'de' yyyy", ptBr))?.capitalized().orEmpty()
    DatePrecision.YEAR -> date?.year?.toString().orEmpty()
    DatePrecision.UNKNOWN -> "Sem data definida"
}

/** Explains how the date was obtained, shown under event titles. */
fun eventDateNote(precision: DatePrecision, suggested: Boolean): String = when {
    precision == DatePrecision.UNKNOWN -> "Nenhuma data foi citada nos relatos"
    suggested -> "Data interpretada a partir do relato · a revisar"
    precision == DatePrecision.DAY -> "Data interpretada a partir do relato"
    precision == DatePrecision.MONTH -> "Mês citado nos relatos · dia não informado"
    else -> "Ano citado nos relatos · mês e dia não informados"
}

fun monthLabel(month: YearMonth): String =
    month.format(DateTimeFormatter.ofPattern("MMMM 'de' yyyy", ptBr)).capitalized()

fun dayLabel(date: LocalDate?): String =
    date?.format(DateTimeFormatter.ofPattern("d 'de' MMMM", ptBr))?.capitalized() ?: "Sem data definida"

fun String.capitalized(): String = replaceFirstChar { it.titlecase(ptBr) }
