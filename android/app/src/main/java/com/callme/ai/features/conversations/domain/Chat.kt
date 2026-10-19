package com.callme.ai.features.conversations.domain

data class ChatMessage(val id: String, val fromUser: Boolean, val text: String)

data class SelectableRecord(val id: String, val label: String)

sealed interface ChatEvent {
    data object Started : ChatEvent
    data class Delta(val text: String) : ChatEvent
    data class Failed(val code: String) : ChatEvent
    data object Completed : ChatEvent
}
