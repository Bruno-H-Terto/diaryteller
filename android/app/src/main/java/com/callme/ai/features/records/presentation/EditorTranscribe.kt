package com.callme.ai.features.records.presentation

import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.callme.ai.R
import com.callme.ai.core.ui.PillButton
import com.callme.ai.features.records.domain.Record
import kotlinx.coroutines.launch

/**
 * Offers on-device transcription when the entry already has a voice note.
 *
 * The recogniser runs with the model shipped in the app, so the recording is
 * never uploaded; the resulting text goes into the entry body like any other
 * transcript.
 */
@Composable
internal fun TranscribeButton(
    record: Record?,
    transcribe: (suspend (String) -> String?)?,
    transcribing: Boolean,
    onTranscribing: (Boolean) -> Unit,
    onTranscript: (String) -> Unit,
) {
    val recordingId = record?.recordingId ?: return
    if (transcribe == null) return
    val scope = rememberCoroutineScope()
    PillButton(
        label = stringResource(
            if (transcribing) R.string.editor_transcribing else R.string.editor_transcribe_audio,
        ),
        onClick = {
            if (transcribing) return@PillButton
            onTranscribing(true)
            scope.launch {
                val text = runCatching { transcribe(recordingId) }.getOrNull()
                if (!text.isNullOrBlank()) onTranscript(text)
                onTranscribing(false)
            }
        },
        tonal = true,
        modifier = Modifier.padding(top = 8.dp),
    )
}
