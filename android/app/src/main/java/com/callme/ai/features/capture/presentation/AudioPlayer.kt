package com.callme.ai.features.capture.presentation

import android.media.MediaPlayer
import java.io.File

/** Plays a decrypted cache file and releases it right after playback. */
class AudioPlayer {
    private var player: MediaPlayer? = null
    private var playing: File? = null

    fun play(file: File) {
        release()
        player = MediaPlayer().apply {
            setDataSource(file.absolutePath)
            setOnCompletionListener { release() }
            prepare()
            start()
        }
        playing = file
    }

    fun release() {
        player?.let { runCatching { it.stop() } }
        player?.release()
        player = null
        playing?.delete()
        playing = null
    }
}
