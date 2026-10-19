package com.callme.ai.core.ui

import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.ui.graphics.Color

/** Brand palette taken from the approved design: forest green, clay accent, warm paper. */
internal object Palette {
    val Green = Color(0xFF24594D)
    val GreenDeep = Color(0xFF1B443B)
    val Clay = Color(0xFF9C4934)
    val Paper = Color(0xFFF7F5EF)
    val Tonal = Color(0xFFE5EDE6)
    val Ink = Color(0xFF242B29)
    val Muted = Color(0xFF5D6863)
    val Hairline = Color(0xFFDDE3DB)
    val White = Color(0xFFFFFFFF)
}

internal val LightColors = lightColorScheme(
    primary = Palette.Green,
    onPrimary = Palette.White,
    primaryContainer = Palette.Tonal,
    onPrimaryContainer = Palette.Green,
    secondary = Palette.Clay,
    onSecondary = Palette.White,
    secondaryContainer = Color(0xFFF3E3DE),
    onSecondaryContainer = Palette.Clay,
    tertiary = Palette.Clay,
    onTertiary = Palette.White,
    background = Palette.Paper,
    onBackground = Palette.Ink,
    surface = Palette.Paper,
    onSurface = Palette.Ink,
    surfaceVariant = Palette.Tonal,
    onSurfaceVariant = Palette.Muted,
    surfaceContainerLowest = Palette.White,
    surfaceContainerLow = Palette.White,
    surfaceContainer = Palette.Tonal,
    surfaceContainerHigh = Palette.Tonal,
    surfaceContainerHighest = Color(0xFFDCE4DD),
    outline = Palette.Muted,
    outlineVariant = Palette.Hairline,
    error = Color(0xFFB3261E),
)

internal val DarkColors = darkColorScheme(
    primary = Color(0xFF9CD3C2),
    onPrimary = Color(0xFF0C2F27),
    primaryContainer = Color(0xFF2A4C43),
    onPrimaryContainer = Color(0xFFD2E9E0),
    secondary = Color(0xFFE5A48F),
    onSecondary = Color(0xFF42201A),
    secondaryContainer = Color(0xFF5A2F25),
    onSecondaryContainer = Color(0xFFFBDDD4),
    tertiary = Color(0xFFE5A48F),
    onTertiary = Color(0xFF42201A),
    background = Color(0xFF14120F),
    onBackground = Color(0xFFEFECE4),
    surface = Color(0xFF14120F),
    onSurface = Color(0xFFEFECE4),
    surfaceVariant = Color(0xFF26302B),
    onSurfaceVariant = Color(0xFFB6BAAE),
    surfaceContainerLowest = Color(0xFF100F0D),
    surfaceContainerLow = Color(0xFF1B1916),
    surfaceContainer = Color(0xFF1F1D19),
    surfaceContainerHigh = Color(0xFF292622),
    surfaceContainerHighest = Color(0xFF33302B),
    outline = Color(0xFF8C9188),
    outlineVariant = Color(0xFF3A3833),
    error = Color(0xFFF2B8B5),
)
