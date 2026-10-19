package com.callme.ai.core.network

import com.google.common.truth.Truth.assertThat
import java.io.StringReader
import org.junit.Test

class SseReaderTest {

    @Test
    fun `frames are separated by blank lines and ignore id lines`() {
        val stream = """
            : keep-alive

            event: started
            data: {"operation_id":"1"}

            event: text_delta
            data: {"text":"Olá"}

            event: text_delta
            data: {"text":" mundo"}

            event: completed
            data: {"state":"succeeded"}

        """.trimIndent()
        val reader = SseReader(StringReader(stream))
        val frames = generateSequence { reader.nextFrame() }.toList()
        assertThat(frames.map { it.event })
            .containsExactly("started", "text_delta", "text_delta", "completed").inOrder()
        assertThat(frames[1].data).isEqualTo("""{"text":"Olá"}""")
    }

    @Test
    fun `heartbeat comments only produce no frame`() {
        val reader = SseReader(StringReader(": keep-alive\n\n"))
        assertThat(reader.nextFrame()).isNull()
    }

    @Test
    fun `truncated stream returns the last complete frame then null`() {
        val reader = SseReader(StringReader("event: started\ndata: {}\n"))
        assertThat(reader.nextFrame()?.event).isEqualTo("started")
        assertThat(reader.nextFrame()).isNull()
    }
}
