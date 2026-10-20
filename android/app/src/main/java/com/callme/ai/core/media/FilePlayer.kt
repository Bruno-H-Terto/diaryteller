package com.callme.ai.core.media

import android.media.MediaPlayer
import java.io.File

/** Plays a decrypted cache file and deletes it as soon as playback ends. */
class FilePlayer(private val onFinished: () -> Unit = {}) {
    private var player: MediaPlayer? = null
    private var playing: File? = null

    fun play(file: File) {
        release()
        playing = file
        player = MediaPlayer().apply {
            setDataSource(file.absolutePath)
            setOnCompletionListener {
                release()
                onFinished()
            }
            prepare()
            start()
        }
    }

    fun release() {
        player?.let { runCatching { it.stop() } }
        player?.release()
        player = null
        playing?.delete()
        playing = null
    }
}
