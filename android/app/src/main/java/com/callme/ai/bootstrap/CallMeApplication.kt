package com.callme.ai.bootstrap

import android.app.Application

class CallMeApplication : Application() {
    lateinit var container: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        container = AppContainer(this)
    }
}
