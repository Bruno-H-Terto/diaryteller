package com.callme.ai.features.capture.presentation

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Close
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import com.callme.ai.R
import com.callme.ai.core.media.FilePlayer
import com.callme.ai.core.ui.LocalSpeaker
import com.callme.ai.features.capture.domain.CaptureMode

/** Voice capture: recording stays on the device, dictation is transcribed offline. */
@Composable
fun CaptureScreen(
    mode: CaptureMode,
    viewModel: CaptureViewModel,
    onSaved: (String) -> Unit,
    onClose: () -> Unit,
) {
    val context = LocalContext.current
    val speaker = remember { LocalSpeaker(context) }
    val player = remember { FilePlayer() }
    DisposableEffect(Unit) {
        onDispose {
            speaker.release()
            player.release()
        }
    }
    val start = {
        when (mode) {
            CaptureMode.DICTATION -> viewModel.startDictation("pt-BR")
            CaptureMode.RECORDING -> viewModel.startRecording()
        }
    }
    val permission = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) start()
    }
    val requestMic = {
        val granted = ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) ==
            PackageManager.PERMISSION_GRANTED
        if (granted) start() else permission.launch(Manifest.permission.RECORD_AUDIO)
    }

    Column(Modifier.fillMaxSize()) {
        Row(Modifier.fillMaxWidth().padding(start = 4.dp, top = 8.dp), verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = onClose, enabled = viewModel.phase != CapturePhase.SAVING) {
                Icon(Icons.Outlined.Close, contentDescription = stringResource(R.string.cd_close))
            }
            Text(
                stringResource(if (mode == CaptureMode.RECORDING) R.string.capture_new_audio else R.string.capture_dictate),
                style = MaterialTheme.typography.titleSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        if (mode == CaptureMode.RECORDING) {
            RecordingPanel(viewModel, requestMic, player, onClose)
        } else {
            DictationPanel(viewModel, requestMic, speaker, onSaved)
        }
    }
}
