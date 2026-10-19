package com.callme.ai.core.ui

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val Light = lightColorScheme(
    primary = Color(0xFF2E5E4E),
    secondary = Color(0xFF6B5B3E),
    surface = Color(0xFFFBF8F3),
)

private val Dark = darkColorScheme(
    primary = Color(0xFF9CCFB9),
    secondary = Color(0xFFD8C39C),
    surface = Color(0xFF141816),
)

@Composable
fun CallMeTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = if (isSystemInDarkTheme()) Dark else Light,
        content = content,
    )
}
