package com.callme.ai.features.settings.presentation

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
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
import com.callme.ai.R

@Composable
fun AccountScreen(email: String, onSignOut: () -> Unit) {
    var confirming by remember { mutableStateOf(false) }
    Column(Modifier.fillMaxSize().padding(24.dp)) {
        Text(stringResource(R.string.account_title), style = MaterialTheme.typography.headlineSmall)
        Text(
            "${stringResource(R.string.account_email)}: $email",
            modifier = Modifier.padding(vertical = 16.dp),
        )
        Button(onClick = { confirming = true }) { Text(stringResource(R.string.account_sign_out)) }
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
