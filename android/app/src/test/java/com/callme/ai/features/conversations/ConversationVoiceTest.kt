package com.callme.ai.features.conversations

import com.callme.ai.features.capture.application.DictationEngine
import com.callme.ai.features.capture.domain.DictationAvailability
import com.callme.ai.features.capture.domain.DictationEvent
import com.callme.ai.features.capture.domain.DictationFailure
import com.callme.ai.features.conversations.presentation.ConversationVoice
import com.google.common.truth.Truth.assertThat
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.runTest
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class ConversationVoiceTest {

    private class FakeEngine(
        private val availability: DictationAvailability = DictationAvailability.AVAILABLE,
    ) : DictationEngine {
        val events = MutableSharedFlow<DictationEvent>(extraBufferCapacity = 8)
        var starts = 0
        var cancelled = 0

        override fun availability() = availability
        override fun events(): Flow<DictationEvent> = events
        override fun start(languageTag: String) {
            starts++
        }
        override fun stop() = Unit
        override fun cancel() {
            cancelled++
        }
        override fun release() = Unit
    }

    @Test
    fun `a final transcript becomes one utterance and partials are forwarded`() = runTest {
        val engine = FakeEngine()
        val partials = mutableListOf<String>()
        val said = mutableListOf<String>()
        val voice = ConversationVoice(
            engine = engine,
            scope = TestScope(UnconfinedTestDispatcher(testScheduler)),
            languageTag = { "pt-BR" },
            onPartial = { partials += it },
            onUtterance = { said += it },
            onUnavailable = { error -> throw AssertionError("unexpected $error") },
        )
        voice.start()
        engine.events.emit(DictationEvent.Partial("conheci o"))
        engine.events.emit(DictationEvent.Final("conheci o Carlos"))

        assertThat(engine.starts).isEqualTo(1)
        assertThat(partials).containsExactly("conheci o", "")
        assertThat(said).containsExactly("conheci o Carlos")
    }

    @Test
    fun `silence restarts listening instead of ending the conversation`() = runTest {
        val engine = FakeEngine()
        val voice = ConversationVoice(
            engine = engine,
            scope = TestScope(UnconfinedTestDispatcher(testScheduler)),
            languageTag = { "pt-BR" },
            onPartial = {},
            onUtterance = {},
            onUnavailable = { error -> throw AssertionError("unexpected $error") },
        )
        voice.start()
        engine.events.emit(DictationEvent.Failed(DictationFailure.SPEECH_TIMEOUT))

        assertThat(engine.starts).isEqualTo(2)
        assertThat(voice.listening).isTrue()
    }

    @Test
    fun `a missing offline pack stops the loop and reports it`() = runTest {
        val engine = FakeEngine(DictationAvailability.MISSING_MODEL)
        var reported: DictationFailure? = null
        val voice = ConversationVoice(
            engine = engine,
            scope = TestScope(UnconfinedTestDispatcher(testScheduler)),
            languageTag = { "pt-BR" },
            onPartial = {},
            onUtterance = {},
            onUnavailable = { reported = it },
        )
        voice.start()

        assertThat(engine.starts).isEqualTo(0)
        assertThat(reported).isEqualTo(DictationFailure.OFFLINE_PACK_MISSING)
        assertThat(voice.listening).isFalse()
    }

    @Test
    fun `stop cancels the recogniser and forgets the partial line`() = runTest {
        val engine = FakeEngine()
        val partials = mutableListOf<String>()
        val voice = ConversationVoice(
            engine = engine,
            scope = TestScope(UnconfinedTestDispatcher(testScheduler)),
            languageTag = { "pt-BR" },
            onPartial = { partials += it },
            onUtterance = {},
            onUnavailable = {},
        )
        voice.start()
        engine.events.emit(DictationEvent.Partial("teste"))
        voice.stop()

        assertThat(engine.cancelled).isEqualTo(1)
        assertThat(partials.last()).isEmpty()
        assertThat(voice.listening).isFalse()
    }
}
