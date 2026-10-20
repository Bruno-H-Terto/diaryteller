package com.callme.ai.features.conversations.application

import com.callme.ai.features.conversations.domain.ChatEvent
import kotlinx.coroutines.flow.Flow

interface ConversationRepository {
    /**
     * Streams one answer and the diary actions it proposes.
     *
     * [recordIds] are the entries the user chose to share; [recordId] is the
     * entry a new event or mention should be attached to, when there is one.
     */
    fun ask(message: String, recordIds: List<String>, recordId: String? = null): Flow<ChatEvent>
}
