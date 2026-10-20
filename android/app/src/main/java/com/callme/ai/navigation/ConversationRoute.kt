package com.callme.ai.navigation

import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavGraphBuilder
import androidx.navigation.compose.composable
import com.callme.ai.features.capture.application.DictationEngine
import com.callme.ai.features.conversations.application.ConversationRepository
import com.callme.ai.features.conversations.application.DiaryMutator
import com.callme.ai.features.conversations.application.ReplySpeaker
import com.callme.ai.features.conversations.domain.SelectableRecord
import com.callme.ai.features.conversations.presentation.ConversationScreen
import com.callme.ai.features.conversations.presentation.ConversationViewModel
import com.callme.ai.features.records.application.RecordsRepository

/** Chat route: shares the local registry so the assistant can reuse and extend it. */
fun NavGraphBuilder.conversationRoute(
    recordsRepository: RecordsRepository,
    conversationRepository: ConversationRepository,
    diaryMutator: DiaryMutator,
    dictation: () -> DictationEngine,
    replySpeaker: () -> ReplySpeaker,
) {
    composable(Destinations.CONVERSATIONS) {
        val vm: ConversationViewModel = viewModel(
            factory = factory {
                ConversationViewModel(
                    repository = conversationRepository,
                    records = recordsRepository,
                    mutator = diaryMutator,
                    dictation = dictation(),
                    speaker = replySpeaker(),
                )
            },
        )
        val rows by recordsRepository.observeRecords().collectAsState(initial = emptyList())
        ConversationScreen(
            viewModel = vm,
            selectable = rows.filter { it.preview.isNotBlank() }
                .map { SelectableRecord(it.id, it.preview.lineSequence().first()) },
        )
    }
}
