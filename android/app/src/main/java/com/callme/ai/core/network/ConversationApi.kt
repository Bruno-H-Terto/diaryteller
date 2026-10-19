package com.callme.ai.core.network

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import okhttp3.ResponseBody
import retrofit2.http.Body
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.Streaming

@Serializable
data class ContextRecordDto(
    val id: String,
    @SerialName("recorded_at") val recordedAt: String,
    val text: String,
    @SerialName("source_type") val sourceType: String = "diary_text",
)

@Serializable
data class ContextBundleDto(
    val coverage: String = "selected_records",
    val records: List<ContextRecordDto>,
)

@Serializable
data class ConversationRequestDto(
    @SerialName("client_message_id") val clientMessageId: String,
    @SerialName("conversation_id") val conversationId: String,
    val mode: String = "conversation",
    val message: String,
    val context: ContextBundleDto,
)

interface ConversationApi {
    /** Streams `text/event-stream`; the body must be consumed incrementally. */
    @Streaming
    @POST("v1/ai/responses")
    suspend fun respond(
        @Header("Idempotency-Key") idempotencyKey: String,
        @Body body: ConversationRequestDto,
    ): ResponseBody
}
