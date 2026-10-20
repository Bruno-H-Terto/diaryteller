package com.callme.ai.features.conversations.presentation

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CalendarMonth
import androidx.compose.material.icons.outlined.Event
import androidx.compose.material.icons.outlined.Group
import androidx.compose.material.icons.outlined.Link
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.callme.ai.R
import com.callme.ai.features.conversations.domain.AppliedChange
import com.callme.ai.features.conversations.domain.AppliedKind

/**
 * What the conversation actually changed in the diary.
 *
 * Showing the applied changes keeps the dialogue honest: the user sees that a
 * name, an event or a date was written, instead of discovering it later.
 */
@OptIn(ExperimentalLayoutApi::class)
@Composable
internal fun ChangeChips(changes: List<AppliedChange>, modifier: Modifier = Modifier) {
    if (changes.isEmpty()) return
    FlowRow(
        modifier = modifier.fillMaxWidth().padding(top = 12.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        changes.forEach { change ->
            Surface(
                shape = RoundedCornerShape(12.dp),
                color = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.6f),
            ) {
                Row(
                    Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                ) {
                    Icon(
                        change.kind.icon(),
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.size(14.dp),
                    )
                    Text(
                        stringResource(change.kind.label(), change.label),
                        style = MaterialTheme.typography.labelMedium,
                    )
                }
            }
        }
    }
}

private fun AppliedKind.icon() = when (this) {
    AppliedKind.ENTITY -> Icons.Outlined.Group
    AppliedKind.EVENT -> Icons.Outlined.Event
    AppliedKind.LINK -> Icons.Outlined.Link
    AppliedKind.DATE -> Icons.Outlined.CalendarMonth
}

private fun AppliedKind.label() = when (this) {
    AppliedKind.ENTITY -> R.string.chat_applied_entity
    AppliedKind.EVENT -> R.string.chat_applied_event
    AppliedKind.LINK -> R.string.chat_applied_link
    AppliedKind.DATE -> R.string.chat_applied_date
}
