package com.callme.ai.features.capture.adapters

import android.media.MediaCodec
import android.media.MediaExtractor
import android.media.MediaFormat
import java.io.ByteArrayOutputStream
import java.io.File
import java.nio.ByteOrder

/**
 * Decodes a recorded file into 16 kHz mono PCM the recogniser understands.
 *
 * Recordings are AAC in an MP4 container, which the speech model cannot read, so
 * the audio is decoded with the platform codec and resampled here. Everything
 * runs on the device; the file is never uploaded.
 */
object AudioFileDecoder {

    fun decode(file: File, sampleRate: Int): ByteArray? {
        val extractor = MediaExtractor()
        var codec: MediaCodec? = null
        return try {
            extractor.setDataSource(file.absolutePath)
            val track = audioTrack(extractor) ?: return null
            extractor.selectTrack(track)
            val format = extractor.getTrackFormat(track)
            val mime = format.getString(MediaFormat.KEY_MIME) ?: return null
            val rate = format.getInteger(MediaFormat.KEY_SAMPLE_RATE)
            val channels = format.getInteger(MediaFormat.KEY_CHANNEL_COUNT).coerceAtLeast(1)
            codec = MediaCodec.createDecoderByType(mime)
            codec.configure(format, null, null, 0)
            codec.start()
            decode(extractor, codec, rate, channels, sampleRate)
        } catch (error: Exception) {
            null
        } finally {
            runCatching { codec?.stop() }
            runCatching { codec?.release() }
            extractor.release()
        }
    }

    private fun audioTrack(extractor: MediaExtractor): Int? =
        (0 until extractor.trackCount).firstOrNull { index ->
            extractor.getTrackFormat(index).getString(MediaFormat.KEY_MIME)
                ?.startsWith("audio/") == true
        }

    private fun decode(
        extractor: MediaExtractor,
        codec: MediaCodec,
        inputRate: Int,
        channels: Int,
        outputRate: Int,
    ): ByteArray {
        val output = ByteArrayOutputStream()
        val info = MediaCodec.BufferInfo()
        var drained = false
        var carry: ShortArray? = null
        while (true) {
            if (!drained) {
                val index = codec.dequeueInputBuffer(TIMEOUT_US)
                if (index >= 0) {
                    val buffer = codec.getInputBuffer(index) ?: return output.toByteArray()
                    val size = extractor.readSampleData(buffer, 0)
                    if (size <= 0) {
                        codec.queueInputBuffer(index, 0, 0, 0, MediaCodec.BUFFER_FLAG_END_OF_STREAM)
                        drained = true
                    } else {
                        codec.queueInputBuffer(index, 0, size, extractor.sampleTime, 0)
                        extractor.advance()
                    }
                }
            }
            val status = codec.dequeueOutputBuffer(info, TIMEOUT_US)
            if (status == MediaCodec.INFO_TRY_AGAIN_LATER || status == MediaCodec.INFO_OUTPUT_FORMAT_CHANGED) {
                continue
            }
            if (status < 0) continue
            codec.getOutputBuffer(status)?.let { buffer ->
                if (info.size > 0) {
                    buffer.position(info.offset)
                    buffer.limit(info.offset + info.size)
                    val mono = toMono(buffer.order(ByteOrder.LITTLE_ENDIAN).asShortBuffer(), channels)
                    val input = carry?.let { mono + it } ?: mono
                    val converted = resample(input, inputRate, outputRate)
                    carry = converted.second
                    converted.first.forEach { sample ->
                        output.write(sample.toInt() and 0xFF)
                        output.write((sample.toInt() shr 8) and 0xFF)
                    }
                }
            }
            codec.releaseOutputBuffer(status, false)
            if (info.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM != 0) break
        }
        return output.toByteArray()
    }

    private fun toMono(samples: java.nio.ShortBuffer, channels: Int): ShortArray {
        val frames = samples.remaining() / channels
        val mono = ShortArray(frames)
        for (frame in 0 until frames) {
            var sum = 0
            repeat(channels) { sum += samples.get().toInt() }
            mono[frame] = (sum / channels).toShort()
        }
        return mono
    }

    /** Linear resampling; speech recognition tolerates it well. */
    private fun resample(input: ShortArray, from: Int, to: Int): Pair<List<Short>, ShortArray?> {
        if (from == to) return input.toList() to null
        val ratio = from.toDouble() / to
        val produced = mutableListOf<Short>()
        var position = 0.0
        while (position + 1 < input.size) {
            val index = position.toInt()
            val fraction = position - index
            val value = input[index] * (1 - fraction) + input[index + 1] * fraction
            produced += value.toInt().toShort()
            position += ratio
        }
        val consumed = position.toInt().coerceAtMost(input.size)
        val remainder = if (consumed < input.size) input.copyOfRange(consumed, input.size) else null
        return produced to remainder
    }

    private const val TIMEOUT_US = 10_000L
}
