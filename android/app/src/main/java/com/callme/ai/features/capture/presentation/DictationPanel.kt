package com.callme.ai.features.capture.presentation

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Mic
import androidx.compose.material.icons.outlined.Stop
import androidx.compose.material.icons.outlined.VolumeUp
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.callme.ai.R
import com.callme.ai.core.ui.LocalSpeaker
import com.callme.ai.core.ui.PillButton
import com.callme.ai.features.capture.domain.DictationAvailability
import com.callme.ai.features.capture.domain.DictationFailure

/** On-device dictation: starts the recogniser, shows the transcript and saves it locally. */
@Composable
internal fun DictationPanel(
    viewModel: CaptureViewModel,
    requestMic: () -> Unit,
    speaker: LocalSpeaker,
    onSaved: (String) -> Unit,
) {
    val listening = viewModel.phase == CapturePhase.LISTENING
    val unavailable = viewModel.availability != DictationAvailability.AVAILABLE
    val toggle = {
        if (listening) viewModel.stopDictation() else requestMic()
    }

    Column(
        Modifier.fillMaxSize().padding(horizontal = 24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Spacer(Modifier.height(32.dp))
        Text(
            stringResource(if (listening) R.string.capture_listening else R.string.capture_tap_to_speak),
            style = MaterialTheme.typography.labelLarge,
            color = if (listening) MaterialTheme.colorScheme.secondary else MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(24.dp))
        Box(
            Modifier
                .size(112.dp)
                .background(MaterialTheme.colorScheme.primary, CircleShape)
                .clickable(enabled = !unavailable || listening, onClick = toggle),
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                if (listening) Icons.Outlined.Stop else Icons.Outlined.Mic,
                contentDescription = stringResource(R.string.cd_mic),
                tint = MaterialTheme.colorScheme.onPrimary,
                modifier = Modifier.size(44.dp),
            )
        }
        Spacer(Modifier.height(16.dp))
        Text(
            stringResource(R.string.capture_dictate_hint),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center,
        )
        Spacer(Modifier.height(24.dp))
        Surface(
            shape = MaterialTheme.shapes.large,
            color = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.6f),
            modifier = Modifier.fillMaxWidth().weight(1f),
        ) {
            Column(Modifier.padding(20.dp)) {
                Text(
                    stringResource(R.string.capture_transcript),
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Text(
                    viewModel.transcript.ifBlank { stringResource(R.string.capture_transcript_hint) },
                    style = MaterialTheme.typography.bodyLarge,
                    color = if (viewModel.transcript.isBlank()) {
                        MaterialTheme.colorScheme.onSurfaceVariant
                    } else {
                        MaterialTheme.colorScheme.onSurface
                    },
                    modifier = Modifier.padding(top = 8.dp),
                )
            }
        }
        if (unavailable) {
            AvailabilityNotice(viewModel.availability)
        }
        viewModel.error?.let { failure ->
            Text(
                stringResource(
                    if (failure == DictationFailure.OFFLINE_PACK_MISSING) {
                        R.string.capture_pack_missing
                    } else {
                        R.string.capture_error
                    },
                    failure.name,
                ),
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.bodySmall,
                modifier = Modifier.padding(top = 12.dp),
            )
        }
        TextButton(
            onClick = { speaker.speak(viewModel.transcript) },
            enabled = viewModel.transcript.isNotBlank(),
        ) {
            Icon(Icons.Outlined.VolumeUp, contentDescription = null, modifier = Modifier.size(18.dp))
            Text(stringResource(R.string.capture_listen), modifier = Modifier.padding(start = 8.dp))
        }
        Row(
            Modifier.fillMaxWidth().padding(bottom = 24.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            PillButton(
                label = stringResource(R.string.capture_discard),
                onClick = viewModel::cancelDictation,
                tonal = true,
                modifier = Modifier.weight(1f),
            )
            PillButton(
                label = stringResource(R.string.capture_done),
                onClick = { viewModel.saveTranscript(onSaved) },
                enabled = viewModel.transcript.isNotBlank() && viewModel.phase != CapturePhase.SAVING,
                modifier = Modifier.weight(1f),
            )
        }
    }
}

@Composable
private fun AvailabilityNotice(availability: DictationAvailability) {
    Text(
        stringResource(
            if (availability == DictationAvailability.MISSING_MODEL) {
                R.string.capture_model_missing
            } else {
                R.string.capture_unsupported
            },
        ),
        style = MaterialTheme.typography.bodySmall,
        color = MaterialTheme.colorScheme.error,
        modifier = Modifier.padding(top = 12.dp),
    )
}
