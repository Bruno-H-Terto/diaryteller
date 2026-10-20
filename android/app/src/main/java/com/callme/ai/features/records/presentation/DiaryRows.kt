package com.callme.ai.features.records.presentation

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.outlined.Mic
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.pluralStringResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.callme.ai.R
import com.callme.ai.core.media.CoverThumbnail
import com.callme.ai.features.capture.domain.CaptureMode
import com.callme.ai.features.records.domain.Record
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale

private val ptBr: Locale = Locale.forLanguageTag("pt-BR")

/** One day of the diary: every record written on that date stays in one card. */
@Composable
internal fun DiaryDayCard(
    date: String,
    records: List<Record>,
    onOpen: (String) -> Unit,
) {
    val day = runCatching { java.time.LocalDate.parse(date) }.getOrNull()
    Surface(
        shape = MaterialTheme.shapes.large,
        color = MaterialTheme.colorScheme.surfaceContainerLowest,
        modifier = Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 6.dp),
    ) {
        Column(Modifier.padding(vertical = 8.dp)) {
            Row(Modifier.padding(horizontal = 16.dp, vertical = 8.dp), verticalAlignment = Alignment.CenterVertically) {
                Text(
                    day?.dayOfMonth?.toString().orEmpty(),
                    style = MaterialTheme.typography.headlineMedium,
                    color = MaterialTheme.colorScheme.secondary,
                )
                Column(Modifier.weight(1f).padding(start = 12.dp)) {
                    Text(
                        day?.format(DateTimeFormatter.ofPattern("EEEE", ptBr))?.replaceFirstChar { it.titlecase(ptBr) }
                            .orEmpty(),
                        style = MaterialTheme.typography.titleSmall,
                    )
                    Text(
                        pluralStringResource(R.plurals.diary_day_count, records.size, records.size),
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
            records.forEachIndexed { index, record ->
                if (index > 0) {
                    HorizontalDivider(Modifier.padding(horizontal = 16.dp), color = MaterialTheme.colorScheme.outlineVariant)
                }
                DiaryRecordRow(record, onClick = { onOpen(record.id) })
            }
        }
    }
}

@Composable
private fun DiaryRecordRow(record: Record, onClick: () -> Unit) {
    val moment = Instant.ofEpochMilli(record.createdAt).atZone(ZoneId.systemDefault())
    val title = record.preview.lineSequence().firstOrNull().orEmpty().ifBlank {
        stringResource(R.string.diary_draft)
    }
    val body = record.preview.lineSequence().drop(1).joinToString(" ").trim()
    Row(
        Modifier.fillMaxWidth().clickable(onClick = onClick).padding(horizontal = 16.dp, vertical = 12.dp),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        if (record.coverUri != null) {
            CoverThumbnail(record.coverUri, size = 56.dp)
        }
        Column(Modifier.weight(1f)) {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(
                    moment.format(DateTimeFormatter.ofPattern("HH:mm")),
                    style = MaterialTheme.typography.labelSmall.copy(fontSize = 11.sp),
                    color = MaterialTheme.colorScheme.secondary,
                )
                if (record.recordingId != null) {
                    Icon(
                        Icons.Outlined.Mic,
                        contentDescription = stringResource(R.string.diary_has_audio),
                        tint = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.size(14.dp),
                    )
                }
            }
            Text(title, style = MaterialTheme.typography.titleSmall, maxLines = 2, overflow = TextOverflow.Ellipsis)
            if (body.isNotBlank()) {
                Text(
                    body,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 3,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.padding(top = 2.dp),
                )
            }
        }
    }
}

/** Floating pill that opens the new-record options. */
@Composable
internal fun NewRecordAction(
    onCreateText: () -> Unit,
    onCapture: (CaptureMode) -> Unit,
    modifier: Modifier = Modifier,
) {
    var menu by remember { mutableStateOf(false) }
    Box(modifier) {
        DropdownMenu(expanded = menu, onDismissRequest = { menu = false }) {
            DropdownMenuItem(
                text = { Text(stringResource(R.string.diary_new_text)) },
                onClick = { menu = false; onCreateText() },
            )
            DropdownMenuItem(
                text = { Text(stringResource(R.string.diary_new_dictation)) },
                onClick = { menu = false; onCapture(CaptureMode.DICTATION) },
            )
            DropdownMenuItem(
                text = { Text(stringResource(R.string.diary_new_recording)) },
                onClick = { menu = false; onCapture(CaptureMode.RECORDING) },
            )
        }
        Surface(
            onClick = { menu = true },
            shape = CircleShape,
            color = MaterialTheme.colorScheme.primary,
            contentColor = MaterialTheme.colorScheme.onPrimary,
            shadowElevation = 6.dp,
        ) {
            Row(
                Modifier.padding(horizontal = 22.dp, vertical = 16.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Icon(Icons.Default.Add, contentDescription = null)
                Text(stringResource(R.string.diary_new_record), style = MaterialTheme.typography.labelLarge)
            }
        }
    }
}
