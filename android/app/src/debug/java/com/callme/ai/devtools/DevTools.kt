package com.callme.ai.devtools

import android.content.Context
import com.callme.ai.bootstrap.CallMeApplication

/**
 * Starts the local control bridge used by the studio panel.
 *
 * The bridge only exists in debug builds. It listens on loopback and expects the
 * developer to expose it with `adb forward tcp:5557 tcp:5557`; nothing is
 * reachable from the network. It never reads diary media, only the state the
 * panel edits.
 */
object DevTools {

    /** Port exposed by `adb forward`; kept in sync with the studio panel. */
    const val PORT = 5557

    /** WAV in the app's files directory the replay engine should speak, if any. */
    @Volatile
    private var replay: String? = null

    fun replayFile(): String? = replay

    fun setReplay(file: String?) {
        replay = file
    }

    fun start(context: Context) {
        val application = context.applicationContext as CallMeApplication
        DevVoice.attach(application)
        DevServer(DevRequest(application.container.database)).start()
    }
}
