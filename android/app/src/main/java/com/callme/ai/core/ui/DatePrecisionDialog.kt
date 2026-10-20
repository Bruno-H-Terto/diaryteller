package com.callme.ai.core.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.callme.ai.R
import com.callme.ai.core.model.DatePrecision

/**
 * Asks only for the parts the narrator actually knows. Choosing "Ano" never
 * fills in a month or day behind the scenes; they are simply not stored.
 */
@Composable
fun DatePrecisionDialog(
    initialYear: Int?,
    initialPrecision: DatePrecision = DatePrecision.YEAR,
    onDismiss: () -> Unit,
    onConfirm: (Int, Int?, Int?, DatePrecision) -> Unit,
    onClear: () -> Unit,
) {
    var year by remember { mutableStateOf(initialYear?.toString().orEmpty()) }
    var month by remember { mutableStateOf("") }
    var day by remember { mutableStateOf("") }
    var precision by remember { mutableStateOf(initialPrecision) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(stringResource(R.string.event_fix_date)) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                val options = listOf(
                    DatePrecision.DAY to R.string.date_day,
                    DatePrecision.MONTH to R.string.date_month,
                    DatePrecision.YEAR to R.string.date_year,
                    DatePrecision.UNKNOWN to R.string.date_unknown,
                )
                options.chunked(2).forEach { row ->
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        row.forEach { (option, label) ->
                            ChoicePill(
                                label = stringResource(label),
                                selected = precision == option,
                                onClick = { precision = option },
                            )
                        }
                    }
                }
                if (precision != DatePrecision.UNKNOWN) {
                    OutlinedTextField(
                        value = year,
                        onValueChange = { year = it.filter(Char::isDigit).take(4) },
                        label = { Text(stringResource(R.string.date_year_field)) },
                        singleLine = true,
                    )
                }
                if (precision == DatePrecision.DAY || precision == DatePrecision.MONTH) {
                    OutlinedTextField(
                        value = month,
                        onValueChange = { month = it.filter(Char::isDigit).take(2) },
                        label = { Text(stringResource(R.string.date_month_field)) },
                        singleLine = true,
                    )
                }
                if (precision == DatePrecision.DAY) {
                    OutlinedTextField(
                        value = day,
                        onValueChange = { day = it.filter(Char::isDigit).take(2) },
                        label = { Text(stringResource(R.string.date_day_field)) },
                        singleLine = true,
                    )
                }
            }
        },
        confirmButton = {
            TextButton(
                onClick = {
                    if (precision == DatePrecision.UNKNOWN) {
                        onClear()
                        return@TextButton
                    }
                    val yearValue = year.toIntOrNull() ?: return@TextButton
                    onConfirm(yearValue, month.toIntOrNull(), day.toIntOrNull(), precision)
                },
            ) { Text(stringResource(R.string.entity_save)) }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text(stringResource(R.string.entity_cancel)) }
        },
    )
}
