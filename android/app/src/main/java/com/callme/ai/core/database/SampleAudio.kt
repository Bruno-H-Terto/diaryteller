package com.callme.ai.core.database

import java.io.File

/** Generates a tiny WAV tone so the synthetic diary has real, playable audio. */
internal object SampleAudio {

    fun tone(seconds: Double = 0.6, sampleRate: Int = 8_000): File {
        val count = (sampleRate * seconds).toInt()
        val target = File.createTempFile("sample-tone", ".wav")
        target.outputStream().use { out ->
            val dataSize = count * 2
            out.write("RIFF".toByteArray())
            out.write(intBytes(36 + dataSize))
            out.write("WAVEfmt ".toByteArray())
            out.write(intBytes(16))
            out.write(shortBytes(1))
            out.write(shortBytes(1))
            out.write(intBytes(sampleRate))
            out.write(intBytes(sampleRate * 2))
            out.write(shortBytes(2))
            out.write(shortBytes(16))
            out.write("data".toByteArray())
            out.write(intBytes(dataSize))
            repeat(count) { index ->
                out.write(shortBytes((Math.sin(index / 12.0) * 2_000).toInt()))
            }
        }
        return target
    }

    private fun intBytes(value: Int) = byteArrayOf(
        (value and 0xFF).toByte(),
        ((value shr 8) and 0xFF).toByte(),
        ((value shr 16) and 0xFF).toByte(),
        ((value shr 24) and 0xFF).toByte(),
    )

    private fun shortBytes(value: Int) = byteArrayOf(
        (value and 0xFF).toByte(),
        ((value shr 8) and 0xFF).toByte(),
    )
}
