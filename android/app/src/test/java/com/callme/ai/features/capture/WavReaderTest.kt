package com.callme.ai.features.capture

import com.callme.ai.features.capture.adapters.WavReader
import com.google.common.truth.Truth.assertThat
import java.io.ByteArrayOutputStream
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class WavReaderTest {

    @get:Rule
    val folder = TemporaryFolder()

    private fun wav(channels: Int, rate: Int, extraChunk: Boolean, payload: ByteArray): File {
        val body = ByteArrayOutputStream()
        body.write("RIFF".toByteArray())
        body.write(int(0))
        body.write("WAVE".toByteArray())
        body.write("fmt ".toByteArray())
        body.write(int(16))
        body.write(short(1))
        body.write(short(channels))
        body.write(int(rate))
        body.write(int(rate * channels * 2))
        body.write(short(channels * 2))
        body.write(short(16))
        if (extraChunk) {
            body.write("LIST".toByteArray())
            body.write(int(4))
            body.write("INFO".toByteArray())
        }
        body.write("data".toByteArray())
        body.write(int(payload.size))
        body.write(payload)
        val file = folder.newFile()
        file.writeBytes(body.toByteArray())
        return file
    }

    private fun int(value: Int) = ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN).putInt(value).array()
    private fun short(value: Int) = ByteBuffer.allocate(2).order(ByteOrder.LITTLE_ENDIAN).putShort(value.toShort()).array()

    @Test
    fun `reads the payload after an unrelated chunk`() {
        val payload = byteArrayOf(1, 2, 3, 4)
        val file = wav(channels = 1, rate = 16_000, extraChunk = true, payload = payload)
        assertThat(WavReader.read(file, 16_000)).isEqualTo(payload)
    }

    @Test
    fun `rejects audio the recogniser cannot use`() {
        val file = wav(channels = 2, rate = 44_100, extraChunk = false, payload = byteArrayOf(1, 2))
        assertThat(WavReader.read(file, 16_000)).isNull()
    }

    @Test
    fun `rejects files that are not wav`() {
        val file = folder.newFile()
        file.writeText("not audio at all")
        assertThat(WavReader.read(file, 16_000)).isNull()
    }
}
