package com.callme.ai.features.records.presentation

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.callme.ai.R

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EditorScreen(
    viewModel: EditorViewModel,
    onBack: () -> Unit,
    onVersions: () -> Unit,
) {
    val versions by viewModel.versions.collectAsStateWithLifecycle()
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.records_new_text)) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = stringResource(R.string.cd_back))
                    }
                },
                actions = {
                    TextButton(onClick = onVersions) { Text(stringResource(R.string.records_versions)) }
                },
            )
        },
    ) { padding ->
        Column(Modifier.fillMaxSize().padding(padding).padding(16.dp)) {
            OutlinedTextField(
                value = viewModel.text,
                onValueChange = viewModel::onTextChange,
                modifier = Modifier.fillMaxWidth().weight(1f),
                placeholder = { Text(stringResource(R.string.records_draft_hint)) },
            )
            Text(
                if (versions.lastOrNull()?.confirmed == true) {
                    stringResource(R.string.records_sync_local)
                } else {
                    stringResource(R.string.records_sync_pending)
                },
                modifier = Modifier.padding(vertical = 8.dp),
            )
            Button(onClick = { viewModel.save(onSaved = onBack) }, modifier = Modifier.fillMaxWidth()) {
                Text(stringResource(R.string.records_save))
            }
        }
    }
}
