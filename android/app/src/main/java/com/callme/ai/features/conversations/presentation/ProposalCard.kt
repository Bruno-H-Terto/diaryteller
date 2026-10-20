package com.callme.ai.features.conversations.presentation

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.pluralStringResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.callme.ai.R
import com.callme.ai.features.conversations.domain.DiaryAction

/** Review gate between an AI suggestion and local diary state. */
@Composable
internal fun ProposalCard(
    actions: List<DiaryAction>,
    onConfirm: () -> Unit,
    onDiscard: () -> Unit,
) {
    if (actions.isEmpty()) return
    Surface(
        color = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.55f),
        shape = RoundedCornerShape(18.dp),
        modifier = Modifier.fillMaxWidth().padding(top = 12.dp),
    ) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(stringResource(R.string.chat_proposal_title), style = MaterialTheme.typography.titleSmall)
            Text(
                pluralStringResource(R.plurals.chat_proposal_count, actions.size, actions.size),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                TextButton(onClick = onDiscard) { Text(stringResource(R.string.chat_proposal_discard)) }
                OutlinedButton(onClick = onConfirm) { Text(stringResource(R.string.chat_proposal_confirm)) }
            }
        }
    }
}
