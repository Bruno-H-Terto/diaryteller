package com.callme.ai.core.ui

import android.content.Context
import android.speech.tts.TextToSpeech
import java.util.Locale

/**
 * Device TTS, so reading text never depends on the backend. Returns the same
 * instance for repeated calls and shuts down with the owning screen.
 */
class LocalSpeaker(private val context: Context) {
    private var engine: TextToSpeech? = null
    private var ready = false

    fun speak(text: String, locale: Locale = Locale("pt", "BR")) {
        val current = engine ?: TextToSpeech(context) { status ->
            ready = status == TextToSpeech.SUCCESS
            engine?.language = locale
        }.also { engine = it }
        if (ready && text.isNotBlank()) {
            current.speak(text, TextToSpeech.QUEUE_FLUSH, null, "callme-${text.hashCode()}")
        }
    }

    fun stop() {
        engine?.stop()
    }

    fun release() {
        engine?.shutdown()
        engine = null
        ready = false
    }
}
