package com.callme.ai.features.capture.domain

/** How voice input is captured. Both paths stay on the device. */
enum class CaptureMode { DICTATION, RECORDING }

/**
 * On-device recognition is the only allowed transcriber. When the device lacks
 * a downloaded model the app must say so instead of uploading audio.
 */
enum class DictationAvailability { AVAILABLE, MISSING_MODEL, UNSUPPORTED_DEVICE }

sealed interface DictationEvent {
    data object Ready : DictationEvent
    data class Partial(val text: String) : DictationEvent
    data class Final(val text: String) : DictationEvent
    data class Failed(val reason: DictationFailure) : DictationEvent
}

enum class DictationFailure {
    NO_MATCH,
    SPEECH_TIMEOUT,
    AUDIO_ERROR,
    BUSY,
    PERMISSION_DENIED,
    CLIENT_ERROR,
    NETWORK_NOT_ALLOWED,
}

data class LocalRecording(
    val id: String,
    val createdAt: Long,
    val durationMs: Long,
    val sizeBytes: Long,
    val recordId: String?,
)

/** Result shown to the user after dictation stops. */
data class DictationDraft(val text: String, val fromPartial: Boolean)
