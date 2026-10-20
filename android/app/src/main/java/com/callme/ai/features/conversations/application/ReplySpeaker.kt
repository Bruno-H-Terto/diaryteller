package com.callme.ai.features.conversations.application

/**
 * Speaks the assistant's answer so a conversation can happen by voice.
 *
 * The device synthesizer is used, so the answer never leaves the phone. The
 * synthesizer is optional: when a device has no voice the chat still works.
 */
interface ReplySpeaker {
    /** Speaks [text], replacing anything still being read. */
    fun speak(text: String)

    fun stop()

    fun release()
}
