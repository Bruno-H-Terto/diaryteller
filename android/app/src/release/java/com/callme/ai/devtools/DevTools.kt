package com.callme.ai.devtools

import android.content.Context

/** Release builds ship no local control surface: the bridge is a debug-only tool. */
object DevTools {
    fun start(context: Context) = Unit
}
