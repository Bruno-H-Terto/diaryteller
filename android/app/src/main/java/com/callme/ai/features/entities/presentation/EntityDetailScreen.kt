package com.callme.ai.features.entities.presentation

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
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
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
import com.callme.ai.core.ui.EntityAvatar
import com.callme.ai.core.ui.PillButton
import com.callme.ai.core.ui.SectionLabel
import com.callme.ai.features.connections.presentation.label
import com.callme.ai.features.connections.presentation.originLabel

/** One entity: identity, factual frequency, related events and source records. */
@Composable
fun EntityDetailScreen(
    viewModel: EntityDetailViewModel,
    onBack: () -> Unit,
    onEdit: () -> Unit,
    onOpenEvent: (String) -> Unit,
    onOpenRecord: (String) -> Unit,
) {
    val profile by viewModel.profile.collectAsStateWithLifecycle()
    val period by viewModel.period.collectAsStateWithLifecycle()
    var editingRelation by remember { mutableStateOf(false) }
    val value = profile
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        Row(Modifier.padding(start = 4.dp, top = 8.dp), verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = onBack) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = stringResource(R.string.cd_back))
            }
            Text(
                stringResource(R.string.tab_connections),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        if (value == null) {
            Text(
                stringResource(R.string.entities_empty),
                modifier = Modifier.padding(24.dp),
                style = MaterialTheme.typography.bodyMedium,
            )
            return@Column
        }
        Column(Modifier.padding(horizontal = 24.dp)) {
            EntityAvatar(value.entity.avatar, size = 96.dp)
            Text(
                value.entity.name,
                style = MaterialTheme.typography.displaySmall,
                modifier = Modifier.padding(top = 16.dp),
            )
            val relation = value.relation
            Text(
                if (relation == null) {
                    stringResource(R.string.relation_unknown)
                } else {
                    "${relation.label.ifBlank { stringResource(R.string.relation_unknown) }} · ${relation.origin.originLabel()}"
                },
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 8.dp),
            )
            Text(
                stringResource(R.string.entity_type, value.entity.type.label()),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            SectionLabel(stringResource(R.string.entity_in_period, period.label), Modifier.padding(top = 24.dp))
            Text(
                stringResource(R.string.entity_period_count, value.periodCount),
                style = MaterialTheme.typography.bodyLarge,
            )
            Text(
                stringResource(R.string.entity_total_count, value.totalCount),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            SectionLabel(stringResource(R.string.entity_events), Modifier.padding(top = 24.dp))
            value.events.forEach { event ->
                Row(
                    Modifier.fillMaxWidth().clickable { onOpenEvent(event.id) }.padding(vertical = 12.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column(Modifier.weight(1f)) {
                        Text(event.title, style = MaterialTheme.typography.titleSmall)
                        Text(
                            event.dateLabel,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                    Icon(Icons.AutoMirrored.Filled.KeyboardArrowRight, contentDescription = null)
                }
            }
            if (value.events.isEmpty()) {
                Text(
                    stringResource(R.string.entity_no_events),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            HorizontalDivider(Modifier.padding(vertical = 16.dp), color = MaterialTheme.colorScheme.outlineVariant)
            value.sources.forEach { source ->
                Row(
                    Modifier.fillMaxWidth().clickable { onOpenRecord(source.recordId) }.padding(vertical = 10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(source.label, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
                    Icon(Icons.AutoMirrored.Filled.KeyboardArrowRight, contentDescription = null)
                }
            }
            PillButton(
                label = stringResource(R.string.entity_edit),
                onClick = onEdit,
                tonal = true,
                modifier = Modifier.fillMaxWidth().padding(top = 20.dp),
            )
            TextButton(
                onClick = { editingRelation = true },
                modifier = Modifier.fillMaxWidth().padding(bottom = 24.dp),
            ) { Text(stringResource(R.string.relation_edit)) }
        }
    }
    if (editingRelation) {
        val current = profile?.relation?.label.orEmpty()
        RelationDialog(
            initial = current,
            onDismiss = { editingRelation = false },
            onConfirm = {
                viewModel.setRelation(it)
                editingRelation = false
            },
        )
    }
}

@Composable
private fun RelationDialog(initial: String, onDismiss: () -> Unit, onConfirm: (String) -> Unit) {
    var label by remember { mutableStateOf(initial) }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(stringResource(R.string.relation_edit)) },
        text = {
            OutlinedTextField(
                value = label,
                onValueChange = { label = it },
                label = { Text(stringResource(R.string.relation_label_field)) },
                singleLine = true,
            )
        },
        confirmButton = {
            TextButton(onClick = { onConfirm(label) }) { Text(stringResource(R.string.entity_save)) }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text(stringResource(R.string.entity_cancel)) }
        },
    )
}
