package com.callme.ai.features.settings.presentation

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.callme.ai.R
import com.callme.ai.core.ui.SectionLabel

/** Explains what never leaves the phone and what the user chose to share with the AI. */
@Composable
fun PrivacyScreen() {
    Column(Modifier.verticalScroll(rememberScrollState()).padding(24.dp)) {
        Text(stringResource(R.string.privacy_headline), style = MaterialTheme.typography.displaySmall)
        SectionLabel(
            stringResource(R.string.privacy_local_label),
            Modifier.padding(top = 32.dp),
        )
        Text(
            stringResource(R.string.privacy_local_body),
            style = MaterialTheme.typography.bodyLarge,
            modifier = Modifier.padding(top = 12.dp),
        )
        HorizontalDivider(
            color = MaterialTheme.colorScheme.outlineVariant,
            modifier = Modifier.padding(vertical = 24.dp),
        )
        SectionLabel(stringResource(R.string.privacy_shared_label))
        Text(
            stringResource(R.string.privacy_shared_body),
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(top = 12.dp),
        )
        Text(
            stringResource(R.string.privacy_note),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(top = 32.dp),
        )
    }
}
