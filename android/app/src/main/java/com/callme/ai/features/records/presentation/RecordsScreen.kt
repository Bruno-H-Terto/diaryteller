package com.callme.ai.features.records.presentation

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.callme.ai.R
import com.callme.ai.features.records.domain.Record
import java.text.DateFormat
import java.util.Date

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RecordsScreen(
    viewModel: RecordsViewModel,
    onOpen: (String) -> Unit,
) {
    val records by viewModel.records.collectAsStateWithLifecycle()
    Scaffold(
        topBar = { TopAppBar(title = { Text(stringResource(R.string.records_title)) }) },
        floatingActionButton = {
            FloatingActionButton(
                onClick = { viewModel.createDraft(onOpen) },
            ) {
                Icon(Icons.Default.Add, contentDescription = stringResource(R.string.cd_new_record))
            }
        },
    ) { padding ->
        if (records.isEmpty()) {
            Text(
                stringResource(R.string.records_empty),
                modifier = Modifier.fillMaxSize().padding(padding).padding(24.dp),
            )
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxSize().padding(padding),
                contentPadding = androidx.compose.foundation.layout.PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                items(records, key = { it.id }) { record ->
                    RecordCard(record, onOpen = { onOpen(record.id) }, onDelete = { viewModel.delete(record.id) })
                }
            }
        }
    }
}

@Composable
private fun RecordCard(record: Record, onOpen: () -> Unit, onDelete: () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth().clickable(onClick = onOpen)) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                record.preview.ifBlank { stringResource(R.string.records_draft_hint) },
                style = MaterialTheme.typography.bodyLarge,
            )
            Text(
                DateFormat.getDateTimeInstance().format(Date(record.updatedAt)),
                style = MaterialTheme.typography.labelSmall,
            )
            IconButton(onClick = onDelete) {
                Icon(Icons.Default.Delete, contentDescription = null)
            }
        }
    }
}
