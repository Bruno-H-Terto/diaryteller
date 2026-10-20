package com.callme.ai.features.connections.presentation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CenterFocusStrong
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import com.callme.ai.R

/** Undo the zoom and the pan applied to the map. */
@Composable
fun RecenterButton(modifier: Modifier = Modifier, onClick: () -> Unit) {
    IconButton(onClick = onClick, modifier = modifier) {
        Icon(
            Icons.Outlined.CenterFocusStrong,
            contentDescription = stringResource(R.string.connections_recenter),
            tint = MaterialTheme.colorScheme.primary,
        )
    }
}

/** Footnote with how many entries the period holds. */
@Composable
fun RecordCountLabel(records: Int, modifier: Modifier = Modifier) {
    Text(
        stringResource(R.string.connections_records, records),
        style = MaterialTheme.typography.labelSmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
        modifier = modifier,
    )
}
