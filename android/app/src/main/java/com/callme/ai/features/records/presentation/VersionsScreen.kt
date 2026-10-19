package com.callme.ai.features.records.presentation

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material.icons.outlined.Check
import androidx.compose.material.icons.outlined.Edit
import androidx.compose.material.icons.outlined.Lock
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.HorizontalDivider
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
import com.callme.ai.core.ui.TonalIcon
import com.callme.ai.features.records.domain.RecordVersion
import com.callme.ai.features.records.domain.VersionOrigin
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale

private val ptBr: Locale = Locale.forLanguageTag("pt-BR")

/** Version history with an explicit restore action that never overwrites the original. */
@Composable
fun VersionsScreen(viewModel: EditorViewModel, onClose: () -> Unit) {
    val versions by viewModel.versions.collectAsStateWithLifecycle()
    var pending by remember { mutableStateOf<RecordVersion?>(null) }
    val newest = versions.maxOfOrNull { it.number } ?: 0

    Column(Modifier.fillMaxSize()) {
        Row(Modifier.fillMaxWidth().padding(start = 4.dp, end = 16.dp, top = 8.dp), verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = onClose) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = stringResource(R.string.cd_back))
            }
        }
        Text(
            stringResource(R.string.versions_title),
            style = MaterialTheme.typography.headlineSmall,
            modifier = Modifier.padding(horizontal = 24.dp),
        )
        Text(
            stringResource(R.string.versions_subtitle),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(horizontal = 24.dp, vertical = 8.dp),
        )
        LazyColumn(Modifier.weight(1f)) {
            items(versions.sortedByDescending { it.number }, key = { it.id }) { version ->
                VersionRow(version, current = version.number == newest) { pending = version }
            }
        }
        TextButton(
            onClick = onClose,
            modifier = Modifier.fillMaxWidth().padding(vertical = 12.dp),
        ) { Text(stringResource(R.string.versions_close)) }
    }
    pending?.let { target ->
        AlertDialog(
            onDismissRequest = { pending = null },
            title = { Text(stringResource(R.string.versions_restore_title, target.number)) },
            text = { Text(stringResource(R.string.versions_restore_body)) },
            confirmButton = {
                TextButton(onClick = {
                    viewModel.restore(target.id)
                    pending = null
                    onClose()
                }) { Text(stringResource(R.string.versions_restore_confirm)) }
            },
            dismissButton = {
                TextButton(onClick = { pending = null }) { Text(stringResource(R.string.versions_cancel)) }
            },
        )
    }
}

@Composable
private fun VersionRow(version: RecordVersion, current: Boolean, onClick: () -> Unit) {
    val icon = when {
        current -> Icons.Outlined.Check
        version.number == 1 -> Icons.Outlined.Lock
        else -> Icons.Outlined.Edit
    }
    Column(Modifier.clickable(onClick = onClick)) {
        Row(
            Modifier.fillMaxWidth().padding(horizontal = 24.dp, vertical = 16.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            TonalIcon(icon)
            Column(Modifier.weight(1f)) {
                Text(
                    buildString {
                        append(if (version.number == 1) stringResource(R.string.versions_original) else "V${version.number}")
                        if (current) append(" · ${stringResource(R.string.versions_current)}")
                    },
                    style = MaterialTheme.typography.titleSmall,
                )
                Text(
                    "${originLabel(version.origin)} · ${timeLabel(version.createdAt)}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Icon(
                Icons.AutoMirrored.Filled.KeyboardArrowRight,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant, modifier = Modifier.padding(horizontal = 24.dp))
    }
}

@Composable
private fun originLabel(origin: VersionOrigin): String = when (origin) {
    VersionOrigin.USER -> stringResource(R.string.versions_origin_user)
    VersionOrigin.AI -> stringResource(R.string.versions_origin_ai)
    VersionOrigin.RESTORE -> stringResource(R.string.versions_origin_restore)
    VersionOrigin.IMPORT -> stringResource(R.string.versions_origin_import)
}

private fun timeLabel(createdAt: Long): String =
    Instant.ofEpochMilli(createdAt)
        .atZone(ZoneId.systemDefault())
        .format(DateTimeFormatter.ofPattern("d MMM · HH:mm", ptBr))
