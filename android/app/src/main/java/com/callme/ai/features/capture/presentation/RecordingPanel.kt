package com.callme.ai.features.capture.presentation

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Check
import androidx.compose.material.icons.outlined.Close
import androidx.compose.material.icons.outlined.Lock
import androidx.compose.material.icons.outlined.Mic
import androidx.compose.material.icons.outlined.PlayArrow
import androidx.compose.material.icons.outlined.Stop
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.callme.ai.R
import com.callme.ai.core.ui.CircleAction

@Composable
internal fun RecordingPanel(
    viewModel: CaptureViewModel,
    requestMic: () -> Unit,
    player: AudioPlayer,
    onClose: () -> Unit,
) {
    val recording = viewModel.phase == CapturePhase.RECORDING
    val last = viewModel.recordings.firstOrNull()
    val hasAudio = recording || last != null

    Column(
        Modifier.fillMaxSize().padding(horizontal = 16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Spacer(Modifier.height(16.dp))
        Text(
            stringResource(
                when {
                    recording -> R.string.capture_recording
                    last != null -> R.string.capture_saved_now
                    else -> R.string.capture_ready
                },
            ),
            style = MaterialTheme.typography.labelLarge,
            color = if (recording) {
                MaterialTheme.colorScheme.secondary
            } else {
                MaterialTheme.colorScheme.onSurfaceVariant
            },
        )
        Text(
            clock(viewModel.elapsedMs),
            style = MaterialTheme.typography.displaySmall.copy(fontSize = 56.sp, letterSpacing = 1.sp),
            modifier = Modifier.padding(top = 8.dp),
        )
        Text(
            stringResource(R.string.capture_pace),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(top = 12.dp),
        )
        Spacer(Modifier.height(28.dp))
        Waveform(active = recording)
        if (!recording && last == null) {
            Spacer(Modifier.height(16.dp))
            Text(
                stringResource(R.string.capture_recording_hint),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center,
                modifier = Modifier.padding(horizontal = 24.dp),
            )
        }
        Spacer(Modifier.weight(1f))
        Row(
            Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceEvenly,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            CircleAction(
                icon = Icons.Outlined.Close,
                label = stringResource(R.string.capture_discard),
                enabled = hasAudio,
                onClick = {
                    player.release()
                    viewModel.discardRecording()
                },
            )
            CircleAction(
                icon = when {
                    recording -> Icons.Outlined.Stop
                    last != null -> Icons.Outlined.PlayArrow
                    else -> Icons.Outlined.Mic
                },
                label = stringResource(
                    when {
                        recording -> R.string.capture_stop
                        last != null -> R.string.capture_play
                        else -> R.string.capture_start
                    },
                ),
                highlighted = true,
                onClick = {
                    if (recording) {
                        viewModel.stopRecording()
                    } else if (last != null) {
                        viewModel.play(last) { file -> player.play(file) }
                    } else {
                        requestMic()
                    }
                },
            )
            CircleAction(
                icon = Icons.Outlined.Check,
                label = stringResource(R.string.capture_done),
                enabled = !recording && last != null,
                onClick = {
                    player.release()
                    onClose()
                },
            )
        }
        Row(
            Modifier.padding(vertical = 20.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Icon(
                Icons.Outlined.Lock,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.size(16.dp),
            )
            Text(
                stringResource(R.string.capture_saved_local),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

private fun clock(millis: Long): String {
    val total = millis / 1000
    return "%02d:%02d".format(total / 60, total % 60)
}
