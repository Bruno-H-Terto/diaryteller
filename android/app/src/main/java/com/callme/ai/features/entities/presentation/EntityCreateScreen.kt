package com.callme.ai.features.entities.presentation

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.callme.ai.R
import com.callme.ai.core.model.AvatarStyle
import com.callme.ai.core.ui.EntityAvatar
import com.callme.ai.core.ui.Motion
import com.callme.ai.core.ui.PillButton
import com.callme.ai.features.connections.presentation.label
import com.callme.ai.features.entities.domain.EntityType

/** Guided local entity creation; the avatar editor continues after identity exists. */
@Composable
fun EntityCreateScreen(
    viewModel: EntitiesViewModel,
    onBack: () -> Unit,
    onCreated: (String) -> Unit,
) {
    var step by remember { mutableIntStateOf(0) }
    var type by remember { mutableStateOf(EntityType.PERSON) }
    var name by remember { mutableStateOf("") }
    Column(Modifier.fillMaxSize()) {
        Row(
            Modifier.fillMaxWidth().padding(start = 8.dp, top = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = if (step == 0) onBack else ({ step = 0 })) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, stringResource(R.string.cd_back))
            }
            Text(
                stringResource(R.string.entity_create_progress, step + 1),
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        AnimatedContent(
            targetState = step,
            transitionSpec = {
                fadeIn(tween(Motion.DISSOLVE_MS)) togetherWith fadeOut(tween(Motion.DISSOLVE_MS))
            },
            label = "entity-create-step",
            modifier = Modifier.weight(1f),
        ) { current ->
            if (current == 0) TypeStep(type, onSelect = { type = it }) else NameStep(type, name) { name = it }
        }
        PillButton(
            label = stringResource(if (step == 0) R.string.action_continue else R.string.entity_create_avatar),
            onClick = if (step == 0) ({ step = 1 }) else ({ viewModel.create(type, name, onCreated) }),
            enabled = step == 0 || name.isNotBlank(),
            modifier = Modifier.fillMaxWidth().padding(24.dp),
        )
    }
}

@Composable
private fun TypeStep(selected: EntityType, onSelect: (EntityType) -> Unit) {
    Column(Modifier.padding(24.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text(stringResource(R.string.entity_create_type_title), style = MaterialTheme.typography.headlineMedium)
        Text(
            stringResource(R.string.entity_create_type_hint),
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        EntityType.entries.filter { it != EntityType.SELF }.forEach { type ->
            val active = type == selected
            Surface(
                color = if (active) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surface,
                shape = RoundedCornerShape(20.dp),
                border = androidx.compose.foundation.BorderStroke(
                    if (active) 2.dp else 1.dp,
                    if (active) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.outlineVariant,
                ),
                modifier = Modifier.fillMaxWidth().clickable { onSelect(type) },
            ) {
                Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                    EntityAvatar(AvatarStyle(type.model(), 0xFFEAE5F6), 52.dp)
                    Text(type.label(), style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(start = 16.dp))
                }
            }
        }
    }
}

@Composable
private fun NameStep(type: EntityType, name: String, onName: (String) -> Unit) {
    Column(Modifier.padding(24.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text(stringResource(R.string.entity_create_name_title), style = MaterialTheme.typography.headlineMedium)
        Text(stringResource(R.string.entity_create_name_hint), style = MaterialTheme.typography.bodyLarge)
        OutlinedTextField(
            value = name,
            onValueChange = onName,
            label = { Text(stringResource(R.string.entity_name)) },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )
    }
}

private fun EntityType.model(): String = when (this) {
    EntityType.PERSON, EntityType.SELF -> "p1"
    EntityType.ANIMAL -> "a1"
    EntityType.PLACE -> "l1"
    EntityType.EVENT -> "e1"
}
