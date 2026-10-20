package com.callme.ai.features.records.presentation

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Mic
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.callme.ai.R
import com.callme.ai.core.media.AudioChoice
import java.text.DateFormat
import java.util.Date

@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun AudioPickerSheet(
    choices: List<AudioChoice>,
    onDismiss: () -> Unit,
    onPick: (AudioChoice) -> Unit,
) {
    androidx.compose.material3.ModalBottomSheet(onDismissRequest = onDismiss) {
        Column(Modifier.padding(start = 24.dp, end = 24.dp, bottom = 24.dp)) {
            Text(
                stringResource(R.string.editor_audio_pick_title),
                style = MaterialTheme.typography.headlineSmall,
            )
            if (choices.isEmpty()) {
                Text(
                    stringResource(R.string.editor_audio_pick_empty),
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.padding(top = 12.dp),
                )
            }
            choices.forEach { choice ->
                Row(
                    Modifier.fillMaxWidth().clickable { onPick(choice) }.padding(vertical = 12.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    Icon(Icons.Outlined.Mic, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                    Text(
                        DateFormat.getDateTimeInstance().format(Date(choice.createdAt)),
                        style = MaterialTheme.typography.bodyMedium,
                        modifier = Modifier.weight(1f),
                    )
                    Text("${choice.durationMs / 1000}s", style = MaterialTheme.typography.bodySmall)
                }
            }
        }
    }
}
