package com.callme.ai.features.conversations.presentation

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.callme.ai.R
import com.callme.ai.core.ui.ChoicePill
import com.callme.ai.features.conversations.domain.SelectableRecord

/** Conversation with the server-side AI, always with an explicit, visible context. */
@Composable
fun ConversationScreen(
    viewModel: ConversationViewModel,
    selectable: List<SelectableRecord>,
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    var input by remember { mutableStateOf("") }
    var selected by remember { mutableStateOf<Set<String>>(emptySet()) }
    var contextOpen by remember { mutableStateOf(false) }
    val listState = rememberLazyListState()

    LaunchedEffect(state.messages.size) {
        if (state.messages.isNotEmpty()) listState.animateScrollToItem(listState.layoutInfo.totalItemsCount)
    }

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        bottomBar = {
            Column {
                state.error?.let { code ->
                    Text(
                        stringResource(R.string.chat_error, code),
                        color = MaterialTheme.colorScheme.error,
                        style = MaterialTheme.typography.bodySmall,
                        modifier = Modifier.padding(horizontal = 24.dp, vertical = 4.dp),
                    )
                }
                MessageComposer(
                    value = input,
                    onValueChange = { input = it },
                    streaming = state.streaming,
                    canSend = input.isNotBlank(),
                    onSend = {
                        viewModel.ask(input, selected)
                        input = ""
                    },
                    onStop = viewModel::cancel,
                    onToggleContext = { contextOpen = !contextOpen },
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 12.dp),
                )
            }
        },
    ) { inner ->
        LazyColumn(
            state = listState,
            modifier = Modifier.fillMaxSize().padding(inner),
            contentPadding = PaddingValues(start = 24.dp, end = 24.dp, top = 16.dp, bottom = 16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            item {
                Column {
                    Text(
                        stringResource(R.string.conversations_title),
                        style = MaterialTheme.typography.headlineLarge,
                    )
                    Text(
                        stringResource(R.string.conversations_subtitle),
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
            if (selectable.isNotEmpty()) {
                item {
                    ContextCard(
                        count = selected.size,
                        expanded = contextOpen,
                        onToggle = { contextOpen = !contextOpen },
                    )
                }
            }
            if (contextOpen) {
                item {
                    LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        items(selectable, key = { it.id }) { record ->
                            ChoicePill(
                                label = record.label.take(32),
                                selected = record.id in selected,
                                onClick = {
                                    selected = if (record.id in selected) {
                                        selected - record.id
                                    } else {
                                        selected + record.id
                                    }
                                },
                            )
                        }
                    }
                }
            }
            item {
                Text(
                    stringResource(R.string.chat_today).uppercase(),
                    style = MaterialTheme.typography.labelSmall.copy(letterSpacing = 1.2.sp),
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.fillMaxWidth(),
                )
            }
            items(state.messages, key = { it.id }) { message ->
                if (message.fromUser) UserBubble(message.text) else AssistantBlock(message.text)
            }
        }
    }
}
