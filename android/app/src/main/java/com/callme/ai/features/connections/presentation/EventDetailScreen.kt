package com.callme.ai.features.connections.presentation

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.outlined.LinkOff
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.callme.ai.R
import com.callme.ai.core.media.CoverThumbnail
import com.callme.ai.core.model.DatePrecision
import com.callme.ai.core.model.eventDateLabel
import com.callme.ai.core.model.eventDateNote
import com.callme.ai.core.ui.DatePrecisionDialog
import com.callme.ai.core.ui.EntityAvatar
import com.callme.ai.core.ui.PillButton
import com.callme.ai.core.ui.SectionLabel

/** Event detail: date with its precision, participants, sources and corrections. */
@Composable
fun EventDetailScreen(
    viewModel: EventViewModel,
    onBack: () -> Unit,
    onOpenRecord: (String) -> Unit,
) {
    val event by viewModel.event.collectAsStateWithLifecycle()
    var correcting by remember { mutableStateOf(false) }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        Row(Modifier.padding(start = 4.dp, top = 8.dp), verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = onBack) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = stringResource(R.string.cd_back))
            }
            Text(
                stringResource(R.string.event_title_label),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        val value = event
        if (value == null) {
            Text(stringResource(R.string.timeline_empty), modifier = Modifier.padding(24.dp))
            return@Column
        }
        Column(Modifier.padding(horizontal = 24.dp)) {
            Text(
                eventDateLabel(value.date, value.precision).uppercase()
                    .ifBlank { stringResource(R.string.event_undated) },
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.secondary,
            )
            Text(value.title, style = MaterialTheme.typography.displaySmall, modifier = Modifier.padding(top = 8.dp))
            Text(
                eventDateNote(value.precision, value.suggested),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 8.dp),
            )
            value.coverUri?.let { CoverThumbnail(it, size = 120.dp, modifier = Modifier.padding(top = 16.dp)) }
            if (value.participants.isNotEmpty()) {
                SectionLabel(stringResource(R.string.event_participants), Modifier.padding(top = 24.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.padding(top = 10.dp)) {
                    (value.participants + listOfNotNull(value.place)).take(4).forEach { person ->
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            EntityAvatar(person.avatar, size = 40.dp)
                            Text(person.name, style = MaterialTheme.typography.labelSmall)
                        }
                    }
                }
            }
            if (value.summary.isNotBlank()) {
                Text(value.summary, style = MaterialTheme.typography.bodyLarge, modifier = Modifier.padding(top = 20.dp))
            }
            SectionLabel(stringResource(R.string.event_sources), Modifier.padding(top = 24.dp))
            value.sources.forEach { source ->
                Row(
                    Modifier.fillMaxWidth().clickable { onOpenRecord(source.recordId) }.padding(vertical = 12.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column(Modifier.weight(1f)) {
                        Text(
                            source.preview.lineSequence().firstOrNull().orEmpty().ifBlank { source.recordId },
                            style = MaterialTheme.typography.bodyMedium,
                            maxLines = 2,
                        )
                        Text(
                            stringResource(
                                R.string.event_recorded_on,
                                source.recordedOn?.format(
                                    java.time.format.DateTimeFormatter.ofPattern(
                                        "d MMM yyyy",
                                        java.util.Locale.forLanguageTag("pt-BR"),
                                    ),
                                )?.replace(".", "").orEmpty(),
                            ),
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                    if (value.sources.size > 1) {
                        IconButton(onClick = { viewModel.detach(source.recordId) }) {
                            Icon(
                                Icons.Outlined.LinkOff,
                                contentDescription = stringResource(R.string.event_detach_source),
                                tint = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    }
                }
            }
            Text(
                stringResource(R.string.event_detach_hint),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            PillButton(
                label = stringResource(R.string.event_fix_date),
                onClick = { correcting = true },
                tonal = true,
                modifier = Modifier.fillMaxWidth().padding(top = 24.dp),
            )
            TextButton(onClick = onBack, modifier = Modifier.fillMaxWidth().padding(bottom = 24.dp)) {
                Text(stringResource(R.string.event_back_timeline))
            }
        }
    }
    if (correcting) {
        DatePrecisionDialog(
            initialYear = viewModel.suggestedYear(),
            onDismiss = { correcting = false },
            initialPrecision = DatePrecision.YEAR,
            onConfirm = { year, month, day, precision ->
                viewModel.setDate(year, month, day, precision)
                correcting = false
            },
            onClear = {
                viewModel.clearDate()
                correcting = false
            },
        )
    }
}
