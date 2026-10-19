package com.callme.ai.features.records.presentation

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
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
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.callme.ai.R
import com.callme.ai.features.capture.domain.CaptureMode
import com.callme.ai.features.records.domain.Record
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale

private val ptBr: Locale = Locale.forLanguageTag("pt-BR")

/** One timeline entry: day column in clay, title, excerpt and time. */
@Composable
internal fun TimelineRow(record: Record, onClick: () -> Unit) {
    val moment = Instant.ofEpochMilli(record.updatedAt).atZone(ZoneId.systemDefault())
    val title = record.preview.lineSequence().firstOrNull().orEmpty().ifBlank {
        stringResource(R.string.diary_draft)
    }
    val body = record.preview.lineSequence().drop(1).joinToString(" ").trim()
    Row(Modifier.fillMaxWidth().padding(horizontal = 24.dp)) {
        Column(Modifier.width(44.dp).padding(top = 4.dp)) {
            Text(
                moment.format(DateTimeFormatter.ofPattern("dd")),
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.secondary,
            )
            Text(
                moment.format(DateTimeFormatter.ofPattern("MMM", ptBr)).replace(".", "").uppercase(ptBr),
                style = MaterialTheme.typography.labelSmall.copy(letterSpacing = 0.8.sp),
                color = MaterialTheme.colorScheme.secondary,
            )
        }
        Column(Modifier.weight(1f).clickable(onClick = onClick).padding(bottom = 16.dp)) {
            Text(
                title,
                style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.SemiBold),
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
            if (body.isNotBlank()) {
                Text(
                    body,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.padding(top = 4.dp),
                )
            }
            Text(
                moment.format(DateTimeFormatter.ofPattern("HH:mm")),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 8.dp),
            )
            Spacer(Modifier.height(12.dp))
            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
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

/** Today's date as a diary subtitle, capitalised in Portuguese. */
internal fun todayLabel(): String {
    val text = LocalDate.now().format(DateTimeFormatter.ofPattern("EEEE, d 'de' MMMM", ptBr))
    return text.replaceFirstChar { it.titlecase(ptBr) }
}
