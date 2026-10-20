package com.callme.ai.features.capture.adapters

import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Reads the PCM payload of a WAV file, skipping the chunks a recorder may add.
 *
 * Only mono 16-bit PCM at the recogniser's rate is accepted; anything else
 * returns null, so the caller can explain instead of transcribing noise.
 */
object WavReader {

    fun read(file: File, sampleRate: Int): ByteArray? = runCatching {
        val bytes = file.readBytes()
        if (bytes.size < 44 || ascii(bytes, 0) != "RIFF" || ascii(bytes, 8) != "WAVE") return null
        var offset = 12
        var mono16 = false
        var rate = 0
        while (offset + 8 <= bytes.size) {
            val id = ascii(bytes, offset)
            val size = littleEndianInt(bytes, offset + 4)
            if (size < 0) return null
            val body = offset + 8
            when (id) {
                "fmt " -> {
                    val channels = littleEndianShort(bytes, body + 2)
                    rate = littleEndianInt(bytes, body + 4)
                    val bits = littleEndianShort(bytes, body + 14)
                    mono16 = channels == 1 && bits == 16
                }
                "data" -> {
                    if (!mono16 || rate != sampleRate) return null
                    val end = (body + size).coerceAtMost(bytes.size)
                    return bytes.copyOfRange(body, end)
                }
            }
            offset = body + size + (size and 1)
        }
        null
    }.getOrNull()

    private fun ascii(bytes: ByteArray, offset: Int): String =
        String(bytes, offset, 4, Charsets.US_ASCII)

    private fun littleEndianInt(bytes: ByteArray, offset: Int): Int =
        ByteBuffer.wrap(bytes, offset, 4).order(ByteOrder.LITTLE_ENDIAN).int

    private fun littleEndianShort(bytes: ByteArray, offset: Int): Int =
        ByteBuffer.wrap(bytes, offset, 2).order(ByteOrder.LITTLE_ENDIAN).short.toInt()
}
