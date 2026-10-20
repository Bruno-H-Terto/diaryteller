package com.callme.ai.bootstrap

import android.app.Application
import com.callme.ai.devtools.DevTools

class CallMeApplication : Application() {
    lateinit var container: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        container = AppContainer(this)
        DevTools.start(this)
    }
}
