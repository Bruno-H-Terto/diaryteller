package com.callme.ai.features.capture.adapters

import java.io.File
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.vosk.Recognizer

/**
 * Transcribes a recorded file on the device, without the microphone.
 *
 * The capture screen uses it to turn an existing voice note into text, and the
 * debug bridge uses it to rehearse the voice loop on a machine without a mic.
 * WAV is read directly and recorded AAC is decoded on the device; anything the
 * platform cannot decode returns null so the UI can explain instead of guessing.
 */
class VoskFileTranscriber(private val model: VoskModel) {

    /** Returns the transcript, or null when the file cannot be read locally. */
    suspend fun transcribe(file: File): String? = withContext(Dispatchers.IO) {
        val loaded = model.await() ?: return@withContext null
        val samples = WavReader.read(file, SAMPLE_RATE)
            ?: AudioFileDecoder.decode(file, SAMPLE_RATE)
            ?: return@withContext null
        val recognizer = runCatching { Recognizer(loaded, SAMPLE_RATE.toFloat()) }.getOrNull()
            ?: return@withContext null
        try {
            val buffer = ByteArray(CHUNK)
            var offset = 0
            while (offset < samples.size) {
                val length = minOf(CHUNK, samples.size - offset)
                System.arraycopy(samples, offset, buffer, 0, length)
                recognizer.acceptWaveForm(buffer, length)
                offset += length
            }
            textOf(recognizer.finalResult)
        } finally {
            recognizer.close()
        }
    }

    private fun textOf(json: String): String {
        val start = json.indexOf("\"text\"")
        if (start < 0) return ""
        val open = json.indexOf('"', start + 7)
        val close = json.lastIndexOf('"')
        return if (open in 0 until close) json.substring(open + 1, close).trim() else ""
    }

    private companion object {
        const val SAMPLE_RATE = 16_000
        const val CHUNK = 8_192
    }
}
