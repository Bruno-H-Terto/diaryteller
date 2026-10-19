package com.callme.ai

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.compose.runtime.mutableStateOf
import com.callme.ai.bootstrap.CallMeApplication
import com.callme.ai.core.ui.CallMeTheme

class MainActivity : ComponentActivity() {
    private val redirect = mutableStateOf<Uri?>(null)

    override fun onCreate(savedInstanceState: Bundle?) {
        installSplashScreen()
        super.onCreate(savedInstanceState)
        redirect.value = intent.redirect()
        val container = (application as CallMeApplication).container
        setContent {
            CallMeTheme {
                AppRoot(container, redirect.value) { redirect.value = null }
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        redirect.value = intent.redirect()
    }

    private fun Intent.redirect(): Uri? =
        data?.takeIf { it.scheme == "callmeai" && it.host == "oidc" }
}
