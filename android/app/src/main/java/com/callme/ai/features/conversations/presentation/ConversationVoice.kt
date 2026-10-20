package com.callme.ai.features.conversations.presentation

import com.callme.ai.features.capture.application.DictationEngine
import com.callme.ai.features.capture.domain.DictationEvent
import com.callme.ai.features.capture.domain.DictationFailure
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch

/**
 * Hands-free turn taking: listen, send what was said, speak the answer, listen
 * again.
 *
 * Recognition and synthesis both run on the device. A turn ends when the
 * recogniser reports a final transcript; silence or a missed phrase simply
 * restarts listening, so the user can talk without pressing anything.
 */
class ConversationVoice(
    private val engine: DictationEngine,
    private val scope: CoroutineScope,
    private val languageTag: () -> String,
    private val onPartial: (String) -> Unit,
    private val onUtterance: (String) -> Unit,
    private val onUnavailable: (DictationFailure) -> Unit,
) {

    var listening: Boolean = false
        private set

    private var job: Job? = null

    fun start() {
        if (listening) return
        listening = true
        job = scope.launch {
            engine.events().collect { event ->
                when (event) {
                    is DictationEvent.Ready -> Unit
                    is DictationEvent.Partial -> onPartial(event.text)
                    is DictationEvent.Final -> {
                        onPartial("")
                        onUtterance(event.text)
                    }
                    is DictationEvent.Failed -> handle(event.reason)
                }
            }
        }
        listen()
    }

    /** Called when the answer finished; keeps the microphone cycle going. */
    fun resume() {
        if (listening) listen()
    }

    fun stop() {
        listening = false
        onPartial("")
        job?.cancel()
        job = null
        engine.cancel()
    }

    private fun listen() {
        if (!listening) return
        when (engine.availability()) {
            com.callme.ai.features.capture.domain.DictationAvailability.AVAILABLE ->
                engine.start(languageTag())
            com.callme.ai.features.capture.domain.DictationAvailability.MISSING_MODEL ->
                fail(DictationFailure.OFFLINE_PACK_MISSING)
            com.callme.ai.features.capture.domain.DictationAvailability.UNSUPPORTED_DEVICE ->
                fail(DictationFailure.CLIENT_ERROR)
        }
    }

    private fun handle(reason: DictationFailure) {
        if (reason == DictationFailure.NO_MATCH || reason == DictationFailure.SPEECH_TIMEOUT) {
            listen()
            return
        }
        fail(reason)
    }

    private fun fail(reason: DictationFailure) {
        onUnavailable(reason)
        listening = false
    }
}
