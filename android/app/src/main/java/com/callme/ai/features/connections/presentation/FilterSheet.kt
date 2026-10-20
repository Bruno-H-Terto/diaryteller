package com.callme.ai.features.connections.presentation

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.callme.ai.R
import com.callme.ai.core.ui.ChoicePill
import com.callme.ai.core.ui.SectionLabel
import com.callme.ai.features.entities.domain.EntityType
import com.callme.ai.features.entities.presentation.EntityFilters

/** Search and type filters, applied to map and timeline alike. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FilterSheet(
    selected: EntityType?,
    query: String,
    onQuery: (String) -> Unit,
    onSelect: (EntityType?) -> Unit,
    onDismiss: () -> Unit,
) {
    ModalBottomSheet(onDismissRequest = onDismiss) {
        Column(Modifier.padding(start = 24.dp, end = 24.dp, bottom = 32.dp)) {
            Text(stringResource(R.string.connections_filters), style = MaterialTheme.typography.headlineSmall)
            OutlinedTextField(
                value = query,
                onValueChange = onQuery,
                placeholder = { Text(stringResource(R.string.connections_search)) },
                singleLine = true,
                modifier = Modifier.fillMaxWidth().padding(top = 16.dp),
            )
            SectionLabel(stringResource(R.string.connections_type), Modifier.padding(top = 20.dp))
            Row(
                Modifier.fillMaxWidth().padding(top = 10.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                ChoicePill(stringResource(R.string.filter_all), selected == null, { onSelect(null) })
            }
            Row(
                Modifier.fillMaxWidth().padding(top = 8.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                EntityFilters.entries.take(2).forEach { filter ->
                    ChoicePill(
                        label = filter.label(),
                        selected = selected == filter.type,
                        onClick = { onSelect(if (selected == filter.type) null else filter.type) },
                    )
                }
            }
            Row(
                Modifier.fillMaxWidth().padding(top = 8.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                EntityFilters.entries.drop(2).forEach { filter ->
                    ChoicePill(
                        label = filter.label(),
                        selected = selected == filter.type,
                        onClick = { onSelect(if (selected == filter.type) null else filter.type) },
                    )
                }
            }
        }
    }
}
