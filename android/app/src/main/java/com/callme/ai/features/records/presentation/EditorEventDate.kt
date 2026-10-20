package com.callme.ai.features.records.presentation

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.callme.ai.R
import com.callme.ai.core.model.DatePrecision
import com.callme.ai.core.model.eventDateLabel
import com.callme.ai.core.model.eventDateNote
import com.callme.ai.core.ui.PillButton
import com.callme.ai.core.ui.SectionLabel
import com.callme.ai.features.records.domain.Record

/** Narrated date of the record, kept separate from the day it was written. */
@Composable
internal fun EditorEventDate(record: Record?, onSet: () -> Unit) {
    SectionLabel(stringResource(R.string.editor_event_date), Modifier.padding(top = 24.dp))
    Row(
        Modifier.fillMaxWidth().padding(top = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Column(Modifier.weight(1f)) {
            record?.let { current ->
                val precision = current.eventDatePrecision
                Text(
                    if (precision == DatePrecision.UNKNOWN) {
                        stringResource(R.string.editor_event_date_unset)
                    } else {
                        eventDateLabel(current.eventDate?.let { parseIso(it) }, precision)
                    },
                    style = MaterialTheme.typography.bodyMedium,
                )
                Text(
                    eventDateNote(precision, false),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
        PillButton(
            label = stringResource(R.string.editor_event_date_set),
            onClick = onSet,
            tonal = true,
        )
    }
    Text(
        stringResource(R.string.editor_event_date_note),
        style = MaterialTheme.typography.bodySmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
        modifier = Modifier.padding(top = 8.dp),
    )
}

internal fun parseIso(value: String) =
    runCatching { java.time.LocalDate.parse(value.take(10)) }.getOrNull()
