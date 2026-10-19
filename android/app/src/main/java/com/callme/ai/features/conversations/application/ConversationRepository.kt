package com.callme.ai.features.conversations.application

import com.callme.ai.features.conversations.domain.ChatEvent
import kotlinx.coroutines.flow.Flow

interface ConversationRepository {
    /** Streams one answer; the message is never re-sent by the repository. */
    fun ask(message: String, recordIds: List<String>): Flow<ChatEvent>
}
