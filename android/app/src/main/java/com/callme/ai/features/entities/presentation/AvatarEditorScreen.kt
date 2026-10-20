package com.callme.ai.features.entities.presentation

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.wrapContentWidth
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.callme.ai.R
import com.callme.ai.core.ui.EntityAvatar
import com.callme.ai.core.ui.PillButton
import com.callme.ai.core.ui.SectionLabel
import com.callme.ai.features.entities.domain.EntityType

/** Chooses model and colours. Saving updates the existing entity in place. */
@Composable
fun AvatarEditorScreen(
    viewModel: AvatarEditorViewModel,
    type: EntityType,
    onBack: () -> Unit,
) {
    val avatar by viewModel.avatar.collectAsStateWithLifecycle()
    val name by viewModel.name.collectAsStateWithLifecycle()
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        Row(Modifier.padding(start = 4.dp, top = 8.dp), verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = onBack) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = stringResource(R.string.cd_back))
            }
        }
        Column(Modifier.padding(horizontal = 24.dp)) {
            Text(stringResource(R.string.entity_edit), style = MaterialTheme.typography.headlineSmall)
            Box(Modifier.fillMaxWidth().padding(vertical = 20.dp), contentAlignment = Alignment.Center) {
                EntityAvatar(avatar, size = 112.dp)
            }
            OutlinedTextField(
                value = name,
                onValueChange = viewModel::onNameChange,
                label = { Text(stringResource(R.string.entity_name)) },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )
            SectionLabel(stringResource(R.string.avatar_model), Modifier.padding(top = 20.dp))
            Row(Modifier.padding(top = 10.dp).wrapContentWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                AvatarCatalog.models(type).forEach { model ->
                    val preview = avatar.copy(model = model)
                    Box(
                        Modifier
                            .clip(CircleShape)
                            .border(
                                width = if (avatar.model == model) 2.dp else 1.dp,
                                color = if (avatar.model == model) {
                                    MaterialTheme.colorScheme.primary
                                } else {
                                    MaterialTheme.colorScheme.outlineVariant
                                },
                                shape = CircleShape,
                            )
                            .clickable { viewModel.selectModel(model) }
                            .padding(4.dp),
                    ) { EntityAvatar(preview, size = 52.dp) }
                }
            }
            PaletteRow(
                title = stringResource(R.string.avatar_background),
                colors = AvatarCatalog.backgrounds,
                selected = avatar.background,
                onSelect = viewModel::selectBackground,
            )
            if (AvatarCatalog.editableParts(type)) {
                PaletteRow(
                    title = stringResource(R.string.avatar_skin),
                    colors = AvatarCatalog.skins,
                    selected = avatar.skin ?: AvatarCatalog.skins[1],
                    onSelect = viewModel::selectSkin,
                )
                PaletteRow(
                    title = stringResource(R.string.avatar_hair),
                    colors = AvatarCatalog.hairs,
                    selected = avatar.hair ?: AvatarCatalog.hairs[0],
                    onSelect = viewModel::selectHair,
                )
                PaletteRow(
                    title = stringResource(R.string.avatar_clothing),
                    colors = AvatarCatalog.clothing,
                    selected = avatar.clothing ?: AvatarCatalog.clothing[0],
                    onSelect = viewModel::selectClothing,
                )
            }
            Text(
                stringResource(R.string.avatar_note),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 20.dp),
            )
            PillButton(
                label = stringResource(R.string.entity_save),
                onClick = { viewModel.save(onBack) },
                enabled = name.isNotBlank(),
                modifier = Modifier.fillMaxWidth().padding(vertical = 24.dp),
            )
        }
    }
}

@Composable
private fun PaletteRow(title: String, colors: List<Long>, selected: Long, onSelect: (Long) -> Unit) {
    SectionLabel(title, Modifier.padding(top = 16.dp))
    Row(Modifier.padding(top = 8.dp), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        colors.forEach { value ->
            val isSelected = value == selected
            Box(
                Modifier
                    .size(34.dp)
                    .clip(CircleShape)
                    .background(Color(value))
                    .border(
                        width = if (isSelected) 3.dp else 1.dp,
                        color = if (isSelected) {
                            MaterialTheme.colorScheme.primary
                        } else {
                            MaterialTheme.colorScheme.outlineVariant
                        },
                        shape = CircleShape,
                    )
                    .clickable { onSelect(value) },
            )
        }
    }
}
