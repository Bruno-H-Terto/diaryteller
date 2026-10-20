package com.callme.ai.devtools

import android.content.Context
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import java.io.File
import java.util.Locale
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout

/**
 * Synthesises a phrase with the device voice and writes it to a WAV file.
 *
 * The emulator has no microphone, so the only way to obtain real speech for a
 * rehearsal is to ask the local synthesiser for it. The file is then fed back
 * through the same recogniser the microphone uses.
 */
object DevSpeech {

    fun say(context: Context, text: String, language: String): File? = runBlocking {
        val engine = CompletableDeferred<TextToSpeech>()
        val done = CompletableDeferred<Unit>()
        val holder = arrayOfNulls<TextToSpeech>(1)
        holder[0] = TextToSpeech(context) { status ->
            val created = holder[0]
            if (created == null || status != TextToSpeech.SUCCESS) {
                done.complete(Unit)
            } else {
                engine.complete(created)
            }
        }
        val synthesizer = withTimeout(WAIT_MS) { engine.await() }
        val locale = Locale.forLanguageTag(language)
        if (synthesizer.setLanguage(locale) >= TextToSpeech.LANG_MISSING_DATA) {
            synthesizer.shutdown()
            return@runBlocking null
        }
        val file = File(context.filesDir, OUTPUT)
        synthesizer.setOnUtteranceProgressListener(
            object : UtteranceProgressListener() {
                override fun onStart(utteranceId: String?) = Unit
                override fun onDone(utteranceId: String?) {
                    done.complete(Unit)
                }

                @Deprecated("Deprecated in Java")
                override fun onError(utteranceId: String?) {
                    done.complete(Unit)
                }
            },
        )
        synthesizer.synthesizeToFile(text, null, file, "rehearsal")
        withTimeout(WAIT_MS) { done.await() }
        synthesizer.shutdown()
        file.takeIf { it.length() > 0 }
    }

    private const val OUTPUT = "tts.wav"
    private const val WAIT_MS = 20_000L
}
