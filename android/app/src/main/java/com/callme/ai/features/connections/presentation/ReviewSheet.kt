package com.callme.ai.features.connections.presentation

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.callme.ai.R
import com.callme.ai.core.ui.PillButton
import com.callme.ai.features.connections.domain.ReviewItem
import com.callme.ai.features.connections.domain.ReviewKind

/** Suggestions stay out of the map until the user confirms or discards them. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ReviewSheet(
    items: List<ReviewItem>,
    onDismiss: () -> Unit,
    onConfirm: (ReviewItem) -> Unit,
    onDiscard: (ReviewItem) -> Unit,
) {
    ModalBottomSheet(onDismissRequest = onDismiss) {
        Column(Modifier.padding(start = 24.dp, end = 24.dp, bottom = 24.dp)) {
            Text(stringResource(R.string.review_title), style = MaterialTheme.typography.headlineSmall)
            Text(
                stringResource(R.string.review_hint),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 4.dp),
            )
            if (items.isEmpty()) {
                Text(
                    stringResource(R.string.review_empty),
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.padding(top = 16.dp),
                )
            }
            LazyColumn(Modifier.fillMaxWidth().padding(top = 8.dp)) {
                items(items, key = { "${it.kind}-${it.id}" }) { item ->
                    Column(Modifier.padding(vertical = 10.dp)) {
                        Text(item.kind.label(), style = MaterialTheme.typography.labelSmall)
                        Text(item.title, style = MaterialTheme.typography.titleSmall)
                        Text(
                            item.subtitle,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                        Row(
                            Modifier.fillMaxWidth().padding(top = 8.dp),
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            PillButton(
                                label = stringResource(R.string.review_confirm),
                                onClick = { onConfirm(item) },
                                modifier = Modifier.weight(1f),
                            )
                            PillButton(
                                label = stringResource(R.string.review_discard),
                                onClick = { onDiscard(item) },
                                tonal = true,
                                modifier = Modifier.weight(1f),
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun ReviewKind.label(): String = stringResource(
    when (this) {
        ReviewKind.LINK -> R.string.review_kind_link
        ReviewKind.RELATION -> R.string.review_kind_relation
        ReviewKind.EVENT -> R.string.review_kind_event
    },
)
