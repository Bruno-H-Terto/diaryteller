package com.callme.ai.features.conversations.adapters

import com.callme.ai.core.network.ContextBundleDto
import com.callme.ai.core.network.ContextRecordDto
import com.callme.ai.core.network.ConversationApi
import com.callme.ai.core.network.ConversationRequestDto
import com.callme.ai.core.network.SseFrame
import com.callme.ai.core.network.SseReader
import com.callme.ai.features.conversations.application.ConversationRepository
import com.callme.ai.features.conversations.domain.ChatEvent
import com.callme.ai.features.records.application.RecordsRepository
import java.io.IOException
import java.time.Instant
import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import okhttp3.ResponseBody

/**
 * Streams answers from the backend, which owns the AI provider key. The app
 * only sends the selected records and never talks to the provider directly.
 */
class HttpConversationRepository(
    private val api: ConversationApi,
    private val records: RecordsRepository,
    private val conversationId: String = UUID.randomUUID().toString(),
    private val now: () -> String = { Instant.now().toString() },
) : ConversationRepository {

    private val json = Json { ignoreUnknownKeys = true }

    override fun ask(message: String, recordIds: List<String>): Flow<ChatEvent> = flow {
        val selected = recordIds.mapNotNull { id ->
            records.currentContent(id)?.takeIf { it.isNotBlank() }?.let { text ->
                ContextRecordDto(id = id, recordedAt = now(), text = text)
            }
        }
        val body = ConversationRequestDto(
            clientMessageId = UUID.randomUUID().toString(),
            conversationId = conversationId,
            message = message,
            context = ContextBundleDto(records = selected),
        )
        val response: ResponseBody = try {
            api.respond(idempotencyKey = UUID.randomUUID().toString(), body = body)
        } catch (error: retrofit2.HttpException) {
            emit(ChatEvent.Failed(if (error.code() == 401) "session_expired" else "http_${error.code()}"))
            return@flow
        } catch (error: IOException) {
            emit(ChatEvent.Failed("network"))
            return@flow
        }
        response.use { payload ->
            val reader = SseReader(payload.charStream())
            while (true) {
                val frame = reader.nextFrame() ?: break
                when (frame.event) {
                    "started" -> emit(ChatEvent.Started)
                    "text_delta" -> emit(ChatEvent.Delta(textOf(frame)))
                    "error" -> {
                        emit(ChatEvent.Failed(codeOf(frame)))
                        break
                    }
                    "completed" -> {
                        emit(ChatEvent.Completed)
                        break
                    }
                }
            }
        }
    }.flowOn(Dispatchers.IO)

    private fun textOf(frame: SseFrame): String =
        runCatching { json.parseToJsonElement(frame.data).jsonObject["text"]?.jsonPrimitive?.content }
            .getOrNull().orEmpty()

    private fun codeOf(frame: SseFrame): String =
        runCatching { json.parseToJsonElement(frame.data).jsonObject["code"]?.jsonPrimitive?.content }
            .getOrNull() ?: "provider_unavailable"
}
