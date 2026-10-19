package com.callme.ai.features.capture.presentation

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import com.callme.ai.R
import com.callme.ai.core.ui.LocalSpeaker
import com.callme.ai.features.capture.domain.CaptureMode
import com.callme.ai.features.capture.domain.DictationAvailability
import java.text.DateFormat
import java.util.Date

@Composable
fun CaptureScreen(
    mode: CaptureMode,
    viewModel: CaptureViewModel,
    onSaved: (String) -> Unit,
) {
    val context = LocalContext.current
    val speaker = remember { LocalSpeaker(context) }
    val player = remember { AudioPlayer() }
    DisposableEffect(Unit) {
        onDispose {
            speaker.release()
            player.release()
        }
    }
    val permission = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) { granted ->
        if (granted) {
            when (mode) {
                CaptureMode.DICTATION -> viewModel.startDictation("pt-BR")
                CaptureMode.RECORDING -> viewModel.startRecording()
            }
        }
    }
    val requestMic = {
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) ==
            PackageManager.PERMISSION_GRANTED
        ) {
            when (mode) {
                CaptureMode.DICTATION -> viewModel.startDictation("pt-BR")
                CaptureMode.RECORDING -> viewModel.startRecording()
            }
        } else {
            permission.launch(Manifest.permission.RECORD_AUDIO)
        }
    }

    Column(Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        val unavailable = viewModel.availability != DictationAvailability.AVAILABLE
        if (mode == CaptureMode.DICTATION && unavailable) {
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(12.dp)) {
                    Text(stringResource(R.string.capture_offline_only), style = MaterialTheme.typography.titleSmall)
                    Text(
                        stringResource(
                            if (viewModel.availability == DictationAvailability.MISSING_MODEL) {
                                R.string.capture_model_missing
                            } else {
                                R.string.capture_unsupported
                            },
                        ),
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
            }
        }
        if (mode == CaptureMode.DICTATION) {
            DictationSection(viewModel, requestMic, speaker, onSaved)
        } else {
            RecordingSection(viewModel, requestMic, player)
        }
    }
}

@Composable
private fun DictationSection(
    viewModel: CaptureViewModel,
    requestMic: () -> Unit,
    speaker: LocalSpeaker,
    onSaved: (String) -> Unit,
) {
    val listening = viewModel.phase == CapturePhase.LISTENING
    Button(
        onClick = { if (listening) viewModel.stopDictation() else requestMic() },
        enabled = viewModel.availability == DictationAvailability.AVAILABLE,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Text(stringResource(if (listening) R.string.capture_stop else R.string.capture_dictate))
    }
    Text(stringResource(R.string.capture_on_device_hint), style = MaterialTheme.typography.bodySmall)
    OutlinedTextField(
        value = viewModel.transcript,
        onValueChange = { },
        readOnly = true,
        modifier = Modifier.fillMaxWidth(),
        label = { Text(stringResource(R.string.capture_transcript)) },
    )
    viewModel.error?.let { error ->
        Text(
            stringResource(R.string.capture_error, error.name),
            color = MaterialTheme.colorScheme.error,
            style = MaterialTheme.typography.bodySmall,
        )
    }
    Button(
        onClick = { viewModel.saveTranscript(onSaved) },
        enabled = viewModel.transcript.isNotBlank() && viewModel.phase != CapturePhase.SAVING,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Text(stringResource(R.string.capture_save_transcript))
    }
    TextButton(onClick = { speaker.speak(viewModel.transcript) }, enabled = viewModel.transcript.isNotBlank()) {
        Text(stringResource(R.string.capture_listen))
    }
}

@Composable
private fun RecordingSection(viewModel: CaptureViewModel, requestMic: () -> Unit, player: AudioPlayer) {
    val recording = viewModel.phase == CapturePhase.RECORDING
    Button(
        onClick = { if (recording) viewModel.stopRecording() else requestMic() },
        modifier = Modifier.fillMaxWidth(),
    ) {
        Text(stringResource(if (recording) R.string.capture_stop else R.string.capture_record))
    }
    Text(stringResource(R.string.capture_local_only), style = MaterialTheme.typography.bodySmall)
    LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        items(viewModel.recordings, key = { it.id }) { item ->
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(12.dp)) {
                    Text(DateFormat.getDateTimeInstance().format(Date(item.createdAt)))
                    Text("${item.durationMs / 1000}s · ${item.sizeBytes / 1024} KiB")
                    TextButton(onClick = {
                        viewModel.play(item) { file -> player.play(file) }
                    }) { Text(stringResource(R.string.capture_play)) }
                    TextButton(onClick = { viewModel.delete(item) }) {
                        Text(stringResource(R.string.capture_discard))
                    }
                }
            }
        }
    }
}
