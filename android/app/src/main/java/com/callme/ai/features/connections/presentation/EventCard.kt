package com.callme.ai.features.connections.presentation

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Mic
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.callme.ai.R
import com.callme.ai.core.media.CoverThumbnail
import com.callme.ai.core.model.eventDateLabel
import com.callme.ai.core.model.eventDateNote
import com.callme.ai.core.ui.EntityAvatar
import com.callme.ai.features.connections.domain.Participant
import com.callme.ai.features.connections.domain.TimelineEvent

/** One narrated event: date with its precision, people, place and sources. */
@Composable
fun EventCard(
    event: TimelineEvent,
    onOpen: () -> Unit,
    onOpenRecord: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    Surface(
        shape = MaterialTheme.shapes.medium,
        color = MaterialTheme.colorScheme.surfaceContainerLowest,
        modifier = modifier.fillMaxWidth().clickable(onClick = onOpen),
    ) {
        Column(Modifier.padding(16.dp)) {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                if (event.coverUri != null) {
                    CoverThumbnail(event.coverUri, size = 56.dp)
                }
                Column(Modifier.weight(1f)) {
                    Text(
                        eventDateLabel(event.date, event.precision)
                            .uppercase()
                            .ifBlank { stringResource(R.string.event_undated) },
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.secondary,
                    )
                    Text(
                        event.title,
                        style = MaterialTheme.typography.titleMedium,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
            }
            if (event.participants.isNotEmpty() || event.place != null) {
                Row(
                    Modifier.padding(top = 12.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    event.participants.take(3).forEach { Chip(it) }
                    event.place?.let { Chip(it) }
                }
            }
            Text(
                eventDateNote(event.precision, event.suggested),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 10.dp),
            )
            event.sources.firstOrNull()?.let { source ->
                Row(
                    Modifier
                        .fillMaxWidth()
                        .padding(top = 10.dp)
                        .clickable { onOpenRecord(source.recordId) },
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Icon(
                        Icons.Outlined.Mic,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.size(16.dp),
                    )
                    Text(
                        stringResource(
                            if (event.sources.size > 1) R.string.event_open_sources else R.string.event_open_source,
                            event.sources.size,
                        ),
                        style = MaterialTheme.typography.labelLarge,
                        color = MaterialTheme.colorScheme.primary,
                    )
                }
            }
        }
    }
}

@Composable
private fun Chip(participant: Participant) {
    Surface(
        shape = CircleShape,
        color = MaterialTheme.colorScheme.primaryContainer,
        contentColor = MaterialTheme.colorScheme.onPrimaryContainer,
    ) {
        Row(
            Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            EntityAvatar(participant.avatar, size = 22.dp)
            Text(participant.name, style = MaterialTheme.typography.labelMedium, maxLines = 1)
        }
    }
}
