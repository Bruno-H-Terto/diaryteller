package com.callme.ai.features.connections.presentation

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
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
import com.callme.ai.features.connections.domain.ConnectionNode

/** Explains and lists the connections folded into the "+N" bubble. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun GroupSheet(
    nodes: List<ConnectionNode>,
    total: Int,
    onDismiss: () -> Unit,
    onSelect: (ConnectionNode) -> Unit,
) {
    ModalBottomSheet(onDismissRequest = onDismiss) {
        Column(Modifier.padding(start = 24.dp, end = 24.dp, bottom = 24.dp)) {
            Text(
                stringResource(R.string.connections_group_title, total),
                style = MaterialTheme.typography.headlineSmall,
            )
            Text(
                stringResource(R.string.connections_group_hint),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 4.dp, bottom = 12.dp),
            )
            LazyColumn(Modifier.fillMaxWidth()) {
                items(nodes, key = { it.id }) { node ->
                    Row(
                        Modifier.fillMaxWidth().clickable { onSelect(node) }.padding(vertical = 10.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(14.dp),
                    ) {
                        EntityAvatar(node.avatar, size = 40.dp)
                        Column(Modifier.weight(1f)) {
                            Text(node.name, style = MaterialTheme.typography.titleSmall)
                            Text(
                                stringResource(R.string.connections_records, node.recordCount),
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                        Icon(Icons.AutoMirrored.Filled.KeyboardArrowRight, contentDescription = null)
                    }
                }
            }
        }
    }
}
