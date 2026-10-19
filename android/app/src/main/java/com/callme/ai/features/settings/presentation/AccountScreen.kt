package com.callme.ai.features.settings.presentation

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.callme.ai.R
import com.callme.ai.core.ui.PillButton
import com.callme.ai.core.ui.SectionLabel

/** Account screen: identifies the session and offers a confirmed sign out. */
@Composable
fun AccountScreen(email: String, onBack: () -> Unit, onSignOut: () -> Unit) {
    var confirming by remember { mutableStateOf(false) }
    Column(Modifier.padding(horizontal = 24.dp)) {
        Row(Modifier.fillMaxWidth().padding(top = 8.dp), verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = onBack) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = stringResource(R.string.settings_back))
            }
        }
        Text(
            stringResource(R.string.settings_account),
            style = MaterialTheme.typography.displaySmall,
            modifier = Modifier.padding(vertical = 16.dp),
        )
        SectionLabel(stringResource(R.string.account_email))
        Text(email, style = MaterialTheme.typography.bodyLarge, modifier = Modifier.padding(top = 8.dp))
        HorizontalDivider(
            color = MaterialTheme.colorScheme.outlineVariant,
            modifier = Modifier.padding(vertical = 24.dp),
        )
        Text(
            stringResource(R.string.account_sign_out_body),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        PillButton(
            label = stringResource(R.string.account_sign_out),
            onClick = { confirming = true },
            tonal = true,
            modifier = Modifier.padding(top = 24.dp),
        )
    }
    if (confirming) {
        AlertDialog(
            onDismissRequest = { confirming = false },
            title = { Text(stringResource(R.string.account_sign_out)) },
            text = { Text(stringResource(R.string.account_sign_out_body)) },
            confirmButton = {
                TextButton(onClick = { confirming = false; onSignOut() }) {
                    Text(stringResource(R.string.account_sign_out_confirm))
                }
            },
            dismissButton = {
                TextButton(onClick = { confirming = false }) {
                    Text(stringResource(R.string.account_cancel))
                }
            },
        )
    }
}
