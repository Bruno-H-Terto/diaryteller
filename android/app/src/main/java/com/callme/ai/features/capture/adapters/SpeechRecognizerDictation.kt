package com.callme.ai.features.capture.adapters

import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import com.callme.ai.features.capture.application.DictationEngine
import com.callme.ai.features.capture.domain.DictationAvailability
import com.callme.ai.features.capture.domain.DictationEvent
import com.callme.ai.features.capture.domain.DictationFailure
import kotlinx.coroutines.channels.BufferOverflow
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow

/**
 * On-device recognition only. The recognizer is created with
 * `createOnDeviceSpeechRecognizer` and `EXTRA_PREFER_OFFLINE`; there is no
 * fallback to a network engine, because audio must never leave the phone.
 */
class SpeechRecognizerDictation(private val context: Context) : DictationEngine {

    private val _events = MutableSharedFlow<DictationEvent>(
        replay = 0,
        extraBufferCapacity = 16,
        onBufferOverflow = BufferOverflow.DROP_OLDEST,
    )
    override fun events(): Flow<DictationEvent> = _events.asSharedFlow()

    private var recognizer: SpeechRecognizer? = null
    private var listening = false
    private val best = StringBuilder()

    override fun availability(): DictationAvailability {
        if (!SpeechRecognizer.isRecognitionAvailable(context)) {
            return DictationAvailability.UNSUPPORTED_DEVICE
        }
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) {
            return DictationAvailability.UNSUPPORTED_DEVICE
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            !SpeechRecognizer.isOnDeviceRecognitionAvailable(context)
        ) {
            return DictationAvailability.MISSING_MODEL
        }
        return DictationAvailability.AVAILABLE
    }

    override fun start(languageTag: String) {
        if (listening) return
        val created = createRecognizer() ?: return fail(DictationFailure.CLIENT_ERROR)
        best.clear()
        recognizer = created
        created.setRecognitionListener(listener)
        listening = true
        created.startListening(intent(languageTag))
    }

    override fun stop() {
        if (!listening) return
        recognizer?.stopListening()
    }

    override fun cancel() {
        listening = false
        recognizer?.cancel()
        recognizer?.destroy()
        recognizer = null
    }

    override fun release() = cancel()

    private fun createRecognizer(): SpeechRecognizer? =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            runCatching { SpeechRecognizer.createOnDeviceSpeechRecognizer(context) }.getOrNull()
        } else {
            null
        }

    private fun intent(languageTag: String) = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
        putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
        putExtra(RecognizerIntent.EXTRA_LANGUAGE, languageTag)
        putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
        putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
        putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, true)
        putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE, context.packageName)
    }

    private val listener = object : RecognitionListener {
        override fun onReadyForSpeech(params: Bundle?) {
            _events.tryEmit(DictationEvent.Ready)
        }

        override fun onBeginningOfSpeech() = Unit

        override fun onRmsChanged(rmsdB: Float) = Unit

        override fun onBufferReceived(buffer: ByteArray?) = Unit

        override fun onEndOfSpeech() = Unit

        override fun onError(error: Int) {
            listening = false
            fail(error.toFailure())
        }

        override fun onResults(results: Bundle?) {
            listening = false
            val text = results.firstText().ifBlank { best.toString() }
            if (text.isBlank()) {
                fail(DictationFailure.NO_MATCH)
            } else {
                _events.tryEmit(DictationEvent.Final(text))
            }
        }

        override fun onPartialResults(partialResults: Bundle?) {
            partialResults.firstText().takeIf { it.isNotBlank() }?.let { text ->
                best.clear()
                best.append(text)
                _events.tryEmit(DictationEvent.Partial(text))
            }
        }

        override fun onEvent(eventType: Int, params: Bundle?) = Unit
    }

    private fun fail(reason: DictationFailure) {
        _events.tryEmit(DictationEvent.Failed(reason))
    }

    private fun Bundle?.firstText(): String =
        this?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.firstOrNull().orEmpty()

    private fun Int.toFailure(): DictationFailure = when (this) {
        SpeechRecognizer.ERROR_NO_MATCH -> DictationFailure.NO_MATCH
        SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> DictationFailure.SPEECH_TIMEOUT
        SpeechRecognizer.ERROR_AUDIO -> DictationFailure.AUDIO_ERROR
        SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> DictationFailure.BUSY
        SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> DictationFailure.PERMISSION_DENIED
        SpeechRecognizer.ERROR_NETWORK, SpeechRecognizer.ERROR_NETWORK_TIMEOUT ->
            DictationFailure.NETWORK_NOT_ALLOWED
        SpeechRecognizer.ERROR_LANGUAGE_NOT_SUPPORTED,
        SpeechRecognizer.ERROR_LANGUAGE_UNAVAILABLE,
        -> DictationFailure.OFFLINE_PACK_MISSING
        else -> DictationFailure.CLIENT_ERROR
    }
}
