package com.callme.ai.features.entities.presentation

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
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
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.callme.ai.R
import com.callme.ai.core.ui.ChoicePill
import com.callme.ai.core.ui.EntityAvatar
import com.callme.ai.core.ui.PillButton
import com.callme.ai.core.ui.SectionLabel
import com.callme.ai.features.connections.presentation.label
import com.callme.ai.features.entities.domain.DiaryEntity
import com.callme.ai.features.entities.domain.EntityType

/** Local registry: every person, animal, place and date keeps a stable entry. */
@Composable
fun EntityListScreen(
    viewModel: EntitiesViewModel,
    onBack: () -> Unit,
    onOpen: (String) -> Unit,
) {
    val entities by viewModel.entities.collectAsStateWithLifecycle()
    var adding by remember { mutableStateOf(false) }

    Column(Modifier.fillMaxSize()) {
        Row(Modifier.padding(start = 4.dp, top = 8.dp), verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = onBack) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = stringResource(R.string.cd_back))
            }
        }
        Text(
            stringResource(R.string.entities_title),
            style = MaterialTheme.typography.headlineMedium,
            modifier = Modifier.padding(horizontal = 24.dp),
        )
        if (entities.isEmpty()) {
            Text(
                stringResource(R.string.entities_empty),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(24.dp),
            )
        }
        LazyColumn(
            contentPadding = PaddingValues(horizontal = 24.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp),
            modifier = Modifier.weight(1f),
        ) {
            EntityType.entries.filter { it != EntityType.SELF }.forEach { type ->
                val group = entities.filter { it.type == type }
                if (group.isNotEmpty()) {
                    item(key = "header-$type") {
                        SectionLabel(type.label(), Modifier.padding(top = 12.dp))
                    }
                    items(group, key = { it.id }) { entity ->
                        EntityRow(entity, onClick = { onOpen(entity.id) })
                    }
                }
            }
        }
        PillButton(
            label = stringResource(R.string.entities_add),
            onClick = { adding = true },
            modifier = Modifier.fillMaxWidth().padding(24.dp),
        )
    }
    if (adding) {
        AddEntityDialog(
            onDismiss = { adding = false },
            onConfirm = { type, name ->
                adding = false
                viewModel.create(type, name) { id -> onOpen(id) }
            },
        )
    }
}

@Composable
private fun EntityRow(entity: DiaryEntity, onClick: () -> Unit) {
    Row(
        Modifier.fillMaxWidth().clickable(onClick = onClick).padding(vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        EntityAvatar(entity.avatar, size = 44.dp)
        Text(entity.name, style = MaterialTheme.typography.titleSmall, modifier = Modifier.weight(1f))
        Icon(Icons.AutoMirrored.Filled.KeyboardArrowRight, contentDescription = null)
    }
}

@Composable
private fun AddEntityDialog(onDismiss: () -> Unit, onConfirm: (EntityType, String) -> Unit) {
    var type by remember { mutableStateOf(EntityType.PERSON) }
    var name by remember { mutableStateOf("") }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(stringResource(R.string.entity_new_title)) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    EntityType.entries.filter { it != EntityType.SELF }.forEach { candidate ->
                        ChoicePill(candidate.label(), type == candidate, { type = candidate })
                    }
                }
                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    label = { Text(stringResource(R.string.entity_name)) },
                    singleLine = true,
                )
            }
        },
        confirmButton = {
            TextButton(onClick = { onConfirm(type, name) }, enabled = name.isNotBlank()) {
                Text(stringResource(R.string.entity_save))
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text(stringResource(R.string.entity_cancel)) }
        },
    )
}
