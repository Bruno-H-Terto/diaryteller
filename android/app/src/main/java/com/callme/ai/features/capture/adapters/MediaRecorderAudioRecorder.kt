package com.callme.ai.features.capture.adapters

import android.content.Context
import android.media.MediaRecorder
import com.callme.ai.features.capture.application.AudioRecorder
import com.callme.ai.features.capture.application.CapturedAudio
import java.io.File

/**
 * Records AAC/MP4 into the private cache directory. The file is encrypted into
 * app storage as soon as the user keeps the note.
 */
class MediaRecorderAudioRecorder(private val context: Context) : AudioRecorder {

    private var recorder: MediaRecorder? = null
    private var current: File? = null
    private var startedAt = 0L

    override val isRecording: Boolean get() = recorder != null

    override fun start(): File {
        check(recorder == null) { "recorder already running" }
        val file = File.createTempFile("voice-", ".m4a", context.cacheDir)
        val created = if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.S) {
            MediaRecorder(context)
        } else {
            @Suppress("DEPRECATION")
            MediaRecorder()
        }
        created.apply {
            setAudioSource(MediaRecorder.AudioSource.MIC)
            setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
            setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
            setAudioEncodingBitRate(96_000)
            setAudioSamplingRate(44_100)
            setOutputFile(file.absolutePath)
            prepare()
            start()
        }
        recorder = created
        current = file
        startedAt = android.os.SystemClock.elapsedRealtime()
        return file
    }

    override fun stop(): CapturedAudio? {
        val active = recorder ?: return null
        val elapsed = android.os.SystemClock.elapsedRealtime() - startedAt
        runCatching { active.stop() }
        active.release()
        recorder = null
        val file = current ?: return null
        current = null
        return CapturedAudio(file, elapsed)
    }

    override fun cancel() {
        val active = recorder
        if (active != null) {
            runCatching { active.stop() }
            active.release()
            recorder = null
        }
        current?.delete()
        current = null
    }
}
