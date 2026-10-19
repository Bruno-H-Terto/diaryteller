package com.callme.ai.features.records.presentation

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.outlined.Close
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextField
import androidx.compose.material3.TextFieldDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.callme.ai.R
import com.callme.ai.core.ui.ChoicePill
import com.callme.ai.core.ui.Wordmark
import com.callme.ai.features.capture.domain.CaptureMode

/** Diary timeline: groups records by day and offers local search and draft filtering. */
@Composable
fun DiaryScreen(
    viewModel: RecordsViewModel,
    onOpen: (String) -> Unit,
    onCapture: (CaptureMode) -> Unit,
) {
    val records by viewModel.records.collectAsStateWithLifecycle()
    var searching by remember { mutableStateOf(false) }
    var query by remember { mutableStateOf("") }
    var draftsOnly by remember { mutableStateOf(false) }
    val visible = records
        .filter { if (draftsOnly) it.preview.isBlank() else true }
        .filter { query.isBlank() || it.preview.contains(query, ignoreCase = true) }

    Box(Modifier.fillMaxSize()) {
        Column(Modifier.fillMaxSize()) {
            DiaryHeader(searching, query, onQueryChange = { query = it }, onToggleSearch = { searching = !searching })
            Text(
                stringResource(R.string.diary_title),
                style = MaterialTheme.typography.displaySmall,
                modifier = Modifier.padding(horizontal = 24.dp),
            )
            Text(
                todayLabel(),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(horizontal = 24.dp, vertical = 4.dp),
            )
            Row(
                Modifier.padding(horizontal = 24.dp, vertical = 16.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                ChoicePill(stringResource(R.string.diary_filter_all), !draftsOnly, onClick = { draftsOnly = false })
                ChoicePill(stringResource(R.string.diary_filter_drafts), draftsOnly, onClick = { draftsOnly = true })
            }
            if (visible.isEmpty()) {
                Text(
                    stringResource(if (records.isEmpty()) R.string.diary_empty else R.string.diary_no_results),
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(horizontal = 24.dp, vertical = 24.dp),
                )
            } else {
                LazyColumn(contentPadding = PaddingValues(bottom = 120.dp)) {
                    items(visible, key = { it.id }) { record ->
                        TimelineRow(record, onClick = { onOpen(record.id) })
                    }
                }
            }
        }
        if (!searching) {
            NewRecordAction(
                onCreateText = { viewModel.createDraft(onOpen) },
                onCapture = onCapture,
                modifier = Modifier.align(Alignment.BottomEnd).padding(24.dp),
            )
        }
    }
}

@Composable
private fun DiaryHeader(
    searching: Boolean,
    query: String,
    onQueryChange: (String) -> Unit,
    onToggleSearch: () -> Unit,
) {
    Row(
        Modifier.fillMaxWidth().padding(start = 24.dp, end = 12.dp, top = 16.dp, bottom = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        if (searching) {
            TextField(
                value = query,
                onValueChange = onQueryChange,
                placeholder = { Text(stringResource(R.string.diary_search)) },
                singleLine = true,
                shape = CircleShape,
                colors = TextFieldDefaults.colors(
                    focusedContainerColor = MaterialTheme.colorScheme.primaryContainer,
                    unfocusedContainerColor = MaterialTheme.colorScheme.primaryContainer,
                    focusedIndicatorColor = Color.Transparent,
                    unfocusedIndicatorColor = Color.Transparent,
                ),
                modifier = Modifier.weight(1f),
            )
        } else {
            Wordmark(Modifier.weight(1f))
        }
        IconButton(onClick = onToggleSearch) {
            Icon(
                if (searching) Icons.Outlined.Close else Icons.Default.Search,
                contentDescription = stringResource(
                    if (searching) R.string.diary_search_close else R.string.cd_search,
                ),
            )
        }
    }
}
