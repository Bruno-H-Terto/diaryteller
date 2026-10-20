package com.callme.ai.features.connections.presentation

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.callme.ai.R
import com.callme.ai.core.ui.EntityAvatar
import com.callme.ai.core.ui.PillButton
import com.callme.ai.core.ui.SectionLabel
import com.callme.ai.features.connections.domain.ConnectionNode
import com.callme.ai.features.entities.domain.EntityProfile
import com.callme.ai.features.entities.domain.EntityType
import com.callme.ai.features.entities.domain.RelationOrigin

/** Bottom panel of a node: identity, factual frequency and related events. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NodeDetailSheet(
    node: ConnectionNode,
    profile: EntityProfile?,
    periodLabel: String,
    onDismiss: () -> Unit,
    onOpenEntity: () -> Unit,
    onEditEntity: () -> Unit,
    onOpenEvent: (String) -> Unit,
    onOpenRecord: (String) -> Unit,
) {
    ModalBottomSheet(onDismissRequest = onDismiss) {
        Column(Modifier.padding(start = 24.dp, end = 24.dp, bottom = 24.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                EntityAvatar(node.avatar, size = 64.dp)
                Column(Modifier.weight(1f)) {
                    Text(node.name, style = MaterialTheme.typography.headlineSmall)
                    Text(
                        stringResource(R.string.entity_type, node.type.label()),
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
            val label = node.relationLabel.ifBlank { stringResource(R.string.relation_unknown) }
            Text(
                "$label · ${node.origin.originLabel()}",
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 12.dp),
            )
            SectionLabel(stringResource(R.string.entity_in_period, periodLabel), Modifier.padding(top = 24.dp))
            Text(
                stringResource(R.string.entity_period_count, node.recordCount),
                style = MaterialTheme.typography.bodyLarge,
                modifier = Modifier.padding(top = 8.dp),
            )
            profile?.let { value ->
                Text(
                    stringResource(R.string.entity_total_count, value.totalCount),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            val events = profile?.events.orEmpty()
            SectionLabel(stringResource(R.string.entity_events), Modifier.padding(top = 20.dp))
            if (events.isEmpty()) {
                Text(
                    stringResource(R.string.entity_no_events),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(top = 8.dp),
                )
            }
            events.forEach { event ->
                Row(
                    Modifier.fillMaxWidth().padding(top = 12.dp),
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
            val sources = profile?.sources.orEmpty()
            if (sources.isNotEmpty()) {
                PillButton(
                    label = stringResource(R.string.entity_open_sources),
                    onClick = { onOpenRecord(sources.first().recordId) },
                    tonal = true,
                    modifier = Modifier.fillMaxWidth().padding(top = 20.dp),
                )
            }
            PillButton(
                label = stringResource(R.string.entity_open_profile),
                onClick = onOpenEntity,
                modifier = Modifier.fillMaxWidth().padding(top = 12.dp),
            )
            PillButton(
                label = stringResource(R.string.entity_edit),
                onClick = onEditEntity,
                tonal = true,
                modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
            )
        }
    }
}

@Composable
internal fun EntityType.label(): String = stringResource(
    when (this) {
        EntityType.PERSON -> R.string.entity_person
        EntityType.ANIMAL -> R.string.entity_animal
        EntityType.PLACE -> R.string.entity_place
        EntityType.EVENT -> R.string.entity_event
        EntityType.SELF -> R.string.connections_you
    },
)

@Composable
internal fun RelationOrigin.originLabel(): String = stringResource(
    when (this) {
        RelationOrigin.CONFIRMED -> R.string.relation_confirmed
        RelationOrigin.DECLARED -> R.string.relation_declared
        RelationOrigin.SUGGESTED -> R.string.relation_suggested
    },
)
