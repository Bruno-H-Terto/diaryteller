package com.callme.ai.features.settings.presentation

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Lock
import androidx.compose.material.icons.outlined.Science
import androidx.compose.material.icons.outlined.Shield
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.callme.ai.BuildConfig
import com.callme.ai.R
import com.callme.ai.core.ui.SectionLabel
import com.callme.ai.core.ui.SettingRow

/** Settings hub: privacy, data, account and the local sample dataset. */
@Composable
fun SettingsScreen(
    onPrivacy: () -> Unit,
    onAccount: () -> Unit,
    sample: SampleDataViewModel? = null,
) {
    var confirming by remember { mutableStateOf(false) }
    val installed = sample?.installed?.collectAsStateWithLifecycle()?.value ?: false
    Column(Modifier.verticalScroll(rememberScrollState()).padding(horizontal = 24.dp)) {
        Text(
            stringResource(R.string.settings_title),
            style = MaterialTheme.typography.displaySmall,
            modifier = Modifier.padding(top = 24.dp, bottom = 24.dp),
        )
        SectionLabel(stringResource(R.string.settings_section))
        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant, modifier = Modifier.padding(top = 12.dp))
        LanguageSetting()
        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
        SettingRow(
            icon = Icons.Outlined.Shield,
            title = stringResource(R.string.settings_privacy),
            subtitle = stringResource(R.string.settings_privacy_sub),
            onClick = onPrivacy,
        )
        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
        SettingRow(
            icon = Icons.Outlined.Lock,
            title = stringResource(R.string.settings_account),
            subtitle = stringResource(R.string.settings_account_sub),
            onClick = onAccount,
        )
        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
        if (BuildConfig.DEBUG && sample != null) {
            SectionLabel(stringResource(R.string.settings_debug), Modifier.padding(top = 32.dp))
            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant, modifier = Modifier.padding(top = 12.dp))
            SettingRow(
                icon = Icons.Outlined.Science,
                title = stringResource(R.string.settings_sample),
                subtitle = stringResource(
                    if (installed) R.string.settings_sample_remove_sub else R.string.settings_sample_add_sub,
                ),
                onClick = { confirming = true },
            )
            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
        }
    }
    if (confirming && sample != null) {
        AlertDialog(
            onDismissRequest = { confirming = false },
            title = { Text(stringResource(R.string.settings_sample)) },
            text = {
                Text(
                    stringResource(
                        if (installed) R.string.settings_sample_remove_body else R.string.settings_sample_add_body,
                    ),
                )
            },
            confirmButton = {
                TextButton(onClick = {
                    sample.toggle()
                    confirming = false
                }) { Text(stringResource(R.string.entity_save)) }
            },
            dismissButton = {
                TextButton(onClick = { confirming = false }) { Text(stringResource(R.string.entity_cancel)) }
            },
        )
    }
}
