package com.callme.ai.features.settings.presentation

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Lock
import androidx.compose.material.icons.outlined.Shield
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.callme.ai.R
import com.callme.ai.core.ui.SectionLabel
import com.callme.ai.core.ui.SettingRow

/** Settings hub: privacy, data and account in native list rows. */
@Composable
fun SettingsScreen(onPrivacy: () -> Unit, onAccount: () -> Unit) {
    Column(Modifier.verticalScroll(rememberScrollState()).padding(horizontal = 24.dp)) {
        Text(
            stringResource(R.string.settings_title),
            style = MaterialTheme.typography.displaySmall,
            modifier = Modifier.padding(top = 24.dp, bottom = 24.dp),
        )
        SectionLabel(stringResource(R.string.settings_section))
        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant, modifier = Modifier.padding(top = 12.dp))
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
    }
}
