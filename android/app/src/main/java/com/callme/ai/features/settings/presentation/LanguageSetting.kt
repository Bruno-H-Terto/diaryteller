package com.callme.ai.features.settings.presentation

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Language
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.callme.ai.R
import com.callme.ai.core.i18n.AppLanguages
import com.callme.ai.core.i18n.changeLanguage
import com.callme.ai.core.i18n.findActivity
import com.callme.ai.core.ui.SettingRow

/**
 * Language row and picker.
 *
 * The options come from the `android/i18n` catalogues; choosing one stores the tag and
 * recreates the activity, so the whole app is rebuilt with the new catalogue.
 */
@Composable
fun LanguageSetting() {
    val context = LocalContext.current
    val languages = remember(context) { AppLanguages.available(context) }
    val current = AppLanguages.current(context)
    var picking by remember { mutableStateOf(false) }
    SettingRow(
        icon = Icons.Outlined.Language,
        title = stringResource(R.string.settings_language),
        subtitle = languages.firstOrNull { it.tag == current }?.label
            ?: stringResource(R.string.settings_language_sub),
        onClick = { picking = true },
    )
    if (picking) {
        AlertDialog(
            onDismissRequest = { picking = false },
            title = { Text(stringResource(R.string.settings_language)) },
            text = {
                Column(Modifier.verticalScroll(rememberScrollState())) {
                    languages.forEach { language ->
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable {
                                    picking = false
                                    context.findActivity()?.let { changeLanguage(it, language.tag) }
                                }
                                .padding(vertical = 2.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            RadioButton(selected = language.tag == current, onClick = null)
                            Text(language.label, style = MaterialTheme.typography.bodyMedium)
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { picking = false }) { Text(stringResource(R.string.cd_close)) }
            },
        )
    }
}
