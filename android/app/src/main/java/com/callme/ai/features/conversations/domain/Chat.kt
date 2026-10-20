package com.callme.ai.features.conversations.domain

data class ChatMessage(
    val id: String,
    val fromUser: Boolean,
    val text: String,
    val proposals: List<DiaryAction> = emptyList(),
    val changes: List<AppliedChange> = emptyList(),
)

data class SelectableRecord(val id: String, val label: String)

sealed interface ChatEvent {
    data object Started : ChatEvent
    data class Delta(val text: String) : ChatEvent
    data class Proposed(val actions: List<DiaryAction>) : ChatEvent
    data class Failed(val code: String) : ChatEvent
    data object Completed : ChatEvent
}
