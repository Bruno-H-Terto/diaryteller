package com.callme.ai.features.records.presentation

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Delete
import androidx.compose.material.icons.outlined.Mic
import androidx.compose.material.icons.outlined.PlayArrow
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.callme.ai.R
import com.callme.ai.core.media.AudioChoice
import com.callme.ai.core.media.CoverThumbnail
import com.callme.ai.core.media.FilePlayer
import com.callme.ai.core.media.LocalMedia
import com.callme.ai.core.ui.PillButton
import com.callme.ai.core.ui.SectionLabel
import com.callme.ai.features.records.domain.Record
import java.text.DateFormat
import java.util.Date
import kotlinx.coroutines.launch

/**
 * Optional cover and one voice note per record. Audio always shows the
 * record text right below the player as its transcription.
 */
@Composable
fun EditorMedia(
    record: Record?,
    text: String,
    onTranscript: (String) -> Unit = {},
    transcribe: (suspend (String) -> String?)? = null,
) {
    val media = LocalMedia.current
    val scope = rememberCoroutineScope()
    val player = remember { FilePlayer() }
    var transcribing by remember { mutableStateOf(false) }
    var pickingAudio by remember { mutableStateOf(false) }
    var choices by remember { mutableStateOf<List<AudioChoice>>(emptyList()) }
    val picker = rememberLauncherForActivityResult(ActivityResultContracts.PickVisualMedia()) { uri ->
        if (uri != null && record != null) scope.launch { media.attachCover(record.id, uri) }
    }

    SectionLabel(stringResource(R.string.editor_cover), Modifier.padding(top = 20.dp))
    Row(
        Modifier.fillMaxWidth().padding(top = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        if (record?.coverUri != null) {
            CoverThumbnail(record.coverUri, size = 72.dp)
        }
        Column(Modifier.weight(1f)) {
            Text(
                stringResource(R.string.editor_cover_note),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.padding(top = 8.dp)) {
                PillButton(
                    label = stringResource(
                        if (record?.coverUri != null) R.string.editor_cover_change else R.string.editor_cover_add,
                    ),
                    onClick = {
                        picker.launch(PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly))
                    },
                    tonal = true,
                )
                if (record?.coverUri != null) {
                    Icon(
                        Icons.Outlined.Delete,
                        contentDescription = stringResource(R.string.editor_cover_remove),
                        tint = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier
                            .size(40.dp)
                            .clickable { scope.launch { media.removeCover(record.id) } },
                    )
                }
            }
        }
    }

    SectionLabel(stringResource(R.string.editor_audio), Modifier.padding(top = 24.dp))
    val recordingId = record?.recordingId
    if (recordingId == null) {
        Text(
            stringResource(R.string.editor_audio_none),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(top = 6.dp),
        )
        PillButton(
            label = stringResource(R.string.editor_audio_attach),
            onClick = {
                pickingAudio = true
                scope.launch { choices = media.audioChoices() }
            },
            tonal = true,
            modifier = Modifier.fillMaxWidth().padding(top = 10.dp),
        )
    } else {
        Row(
            Modifier.fillMaxWidth().padding(top = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Surface(
                onClick = {
                    scope.launch { media.playable(recordingId)?.let { file -> player.play(file) } }
                },
                shape = CircleShape,
                color = MaterialTheme.colorScheme.primaryContainer,
            ) {
                Icon(
                    Icons.Outlined.PlayArrow,
                    contentDescription = stringResource(R.string.capture_play),
                    tint = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.padding(10.dp),
                )
            }
            Column(Modifier.weight(1f)) {
                Text(
                    stringResource(R.string.editor_audio_label),
                    style = MaterialTheme.typography.titleSmall,
                )
                Text(
                    stringResource(R.string.editor_transcript_note),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Icon(
                Icons.Outlined.Delete,
                contentDescription = stringResource(R.string.editor_audio_remove),
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.size(24.dp).clickable {
                    record?.let { scope.launch { media.attachAudio(it.id, null) } }
                },
            )
        }
        SectionLabel(stringResource(R.string.editor_transcript), Modifier.padding(top = 16.dp))
        TranscribeButton(
            record = record,
            transcribe = transcribe,
            transcribing = transcribing,
            onTranscribing = { transcribing = it },
            onTranscript = onTranscript,
        )
        Text(
            text.ifBlank { stringResource(R.string.editor_transcript_note) },
            style = MaterialTheme.typography.bodyLarge,
            color = if (text.isBlank()) {
                MaterialTheme.colorScheme.onSurfaceVariant
            } else {
                MaterialTheme.colorScheme.onSurface
            },
            modifier = Modifier.padding(top = 6.dp),
        )
    }

    if (pickingAudio) {
        AudioPickerSheet(
            choices = choices,
            onDismiss = { pickingAudio = false },
            onPick = { choice ->
                pickingAudio = false
                record?.let { scope.launch { media.attachAudio(it.id, choice.id) } }
            },
        )
    }
}
