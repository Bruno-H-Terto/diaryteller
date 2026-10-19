package com.callme.ai.core.network

import java.io.BufferedReader
import java.io.Reader

/** Minimal SSE frame: event name plus the raw JSON data line. */
data class SseFrame(val event: String, val data: String)

/**
 * Reads `event:`/`data:` frames until the stream ends, ignoring comments
 * (heartbeats) and `id:` lines. A blank line terminates a frame; a stream that
 * closes without the final blank line still yields its last frame once.
 */
class SseReader(reader: Reader) {
    private val source = BufferedReader(reader)
    private var finished = false

    fun nextFrame(): SseFrame? {
        if (finished) return null
        var event = ""
        val data = StringBuilder()
        while (true) {
            val line = source.readLine()
            if (line == null) {
                finished = true
                return frameOf(event, data)
            }
            when {
                line.isEmpty() -> frameOf(event, data)?.let {
                    finished = false
                    return it
                }.also {
                    event = ""
                    data.setLength(0)
                }
                line.startsWith(":") -> Unit
                line.startsWith("event:") -> event = line.removePrefix("event:").trim()
                line.startsWith("data:") -> data.append(line.removePrefix("data:").trim())
            }
        }
    }

    private fun frameOf(event: String, data: StringBuilder): SseFrame? =
        if (event.isNotEmpty() && data.isNotEmpty()) SseFrame(event, data.toString()) else null
}
