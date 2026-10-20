package com.callme.ai.features.conversations.application

import com.callme.ai.features.conversations.domain.AppliedChange
import com.callme.ai.features.conversations.domain.DiaryAction
import com.callme.ai.features.conversations.domain.DiarySnapshot

/**
 * Reads the local registry for the assistant and applies what it proposes.
 *
 * Both sides stay on the device: the snapshot is sent with a turn and the
 * actions are written back to Room. Nothing else in the app writes diary data
 * from a conversation.
 */
interface DiaryMutator {

    /** Entity and event ids plus today's date, small enough to send every turn. */
    suspend fun snapshot(): DiarySnapshot

    /** Applies validated actions in order and reports what changed. */
    suspend fun apply(actions: List<DiaryAction>, recordId: String?): List<AppliedChange>
}
