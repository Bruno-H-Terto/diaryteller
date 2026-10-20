package com.callme.ai.features.conversations.adapters

import android.content.Context
import android.speech.tts.TextToSpeech
import com.callme.ai.features.conversations.application.ReplySpeaker
import java.util.Locale
import java.util.UUID

/**
 * Device text-to-speech bound to the current app language.
 *
 * Answers are read aloud only; nothing is sent anywhere. When the engine is
 * still initialising the text is spoken as soon as it is ready.
 */
class AndroidReplySpeaker(context: Context, private val locale: Locale) : ReplySpeaker {

    private var engine: TextToSpeech? = null
    private var ready = false
    private var pending: String? = null

    init {
        engine = TextToSpeech(context.applicationContext) { status ->
            ready = status == TextToSpeech.SUCCESS
            if (ready) {
                engine?.language = locale
                pending?.let { speak(it) }
            }
            pending = null
        }
    }

    override fun speak(text: String) {
        val clean = text.trim()
        if (clean.isEmpty()) return
        val synthesizer = engine ?: return
        if (!ready) {
            pending = clean
            return
        }
        synthesizer.speak(clean, TextToSpeech.QUEUE_FLUSH, null, UUID.randomUUID().toString())
    }

    override fun stop() {
        pending = null
        engine?.stop()
    }

    override fun release() {
        pending = null
        engine?.stop()
        engine?.shutdown()
        engine = null
        ready = false
    }
}
