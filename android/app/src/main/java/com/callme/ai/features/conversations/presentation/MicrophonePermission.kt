package com.callme.ai.features.conversations.presentation

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import androidx.core.content.ContextCompat

/**
 * Asks for the microphone the first time the conversation goes hands-free.
 *
 * Without this the recogniser refuses to open the audio input, and the feature
 * that defines the app would silently fail after a fresh install.
 */
@Composable
internal fun rememberMicrophone(onGranted: () -> Unit): () -> Unit {
    val context = LocalContext.current
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) onGranted()
    }
    return remember(context) {
        {
            val allowed = ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) ==
                PackageManager.PERMISSION_GRANTED
            if (allowed) onGranted() else launcher.launch(Manifest.permission.RECORD_AUDIO)
        }
    }
}
