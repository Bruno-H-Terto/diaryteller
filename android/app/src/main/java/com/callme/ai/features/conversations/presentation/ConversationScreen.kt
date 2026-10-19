package com.callme.ai.features.conversations.presentation

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.horizontalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
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
import com.callme.ai.features.conversations.domain.SelectableRecord

@Composable
fun ConversationScreen(
    viewModel: ConversationViewModel,
    selectable: List<SelectableRecord>,
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    var input by remember { mutableStateOf("") }
    var selected by remember { mutableStateOf<Set<String>>(emptySet()) }
    val listState = rememberLazyListState()

    Column(Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        if (selectable.isNotEmpty()) {
            Text(stringResource(R.string.chat_context_hint), style = MaterialTheme.typography.bodySmall)
            Row(
                Modifier.horizontalScroll(rememberScrollState()),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                selectable.forEach { record ->
                    FilterChip(
                        selected = record.id in selected,
                        onClick = {
                            selected = if (record.id in selected) selected - record.id else selected + record.id
                        },
                        label = { Text(record.label.take(28)) },
                    )
                }
            }
        }
        LazyColumn(Modifier.weight(1f), state = listState, verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(state.messages, key = { it.id }) { message ->
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(12.dp)) {
                        Text(
                            if (message.fromUser) {
                                stringResource(R.string.chat_you)
                            } else {
                                stringResource(R.string.chat_assistant)
                            },
                            style = MaterialTheme.typography.labelSmall,
                        )
                        Text(message.text, style = MaterialTheme.typography.bodyMedium)
                    }
                }
            }
        }
        state.error?.let { code ->
            Text(
                stringResource(R.string.chat_error, code),
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.bodySmall,
            )
        }
        OutlinedTextField(
            value = input,
            onValueChange = { input = it },
            modifier = Modifier.fillMaxWidth(),
            label = { Text(stringResource(R.string.chat_message)) },
            maxLines = 4,
        )
        Row(
            Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            if (state.streaming) {
                Button(onClick = viewModel::cancel, modifier = Modifier.weight(1f)) {
                    Text(stringResource(R.string.chat_stop))
                }
            } else {
                Button(
                    onClick = {
                        viewModel.ask(input, selected)
                        input = ""
                    },
                    enabled = input.isNotBlank(),
                    modifier = Modifier.weight(1f),
                ) {
                    Text(stringResource(R.string.chat_send))
                }
            }
        }
    }
}
