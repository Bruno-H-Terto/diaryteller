package com.callme.ai.core.ui

import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.ui.graphics.Color

/**
 * Diaryteller palette: indigo ink on paper, lavender for highlights and a clay
 * accent reserved for dates and warnings.
 */
internal object Palette {
    val Indigo = Color(0xFF51438F)
    val IndigoDeep = Color(0xFF362B70)
    val Lavender = Color(0xFFEAE5F6)
    val Paper = Color(0xFFF7F4F0)
    val Surface = Color(0xFFFFFDF9)
    val Ink = Color(0xFF2B2938)
    val Muted = Color(0xFF686477)
    val Clay = Color(0xFFB86443)
    val Hairline = Color(0xFFE4DFEA)
}

internal val LightColors = lightColorScheme(
    primary = Palette.Indigo,
    onPrimary = Palette.Surface,
    primaryContainer = Palette.Lavender,
    onPrimaryContainer = Palette.IndigoDeep,
    inversePrimary = Color(0xFFCBBFF5),
    secondary = Palette.Clay,
    onSecondary = Palette.Surface,
    secondaryContainer = Color(0xFFF6E4DA),
    onSecondaryContainer = Color(0xFF6B331E),
    tertiary = Color(0xFF4F7D6B),
    onTertiary = Palette.Surface,
    tertiaryContainer = Color(0xFFDCEBE3),
    onTertiaryContainer = Color(0xFF1D4436),
    background = Palette.Paper,
    onBackground = Palette.Ink,
    surface = Palette.Paper,
    onSurface = Palette.Ink,
    surfaceVariant = Palette.Lavender,
    onSurfaceVariant = Palette.Muted,
    surfaceContainerLowest = Palette.Surface,
    surfaceContainerLow = Palette.Surface,
    surfaceContainer = Color(0xFFF2EEF7),
    surfaceContainerHigh = Color(0xFFEDE8F4),
    surfaceContainerHighest = Color(0xFFE6E0F0),
    outline = Palette.Muted,
    outlineVariant = Palette.Hairline,
    error = Color(0xFFB3261E),
    onError = Palette.Surface,
    errorContainer = Color(0xFFF9DEDC),
    onErrorContainer = Color(0xFF410E0B),
)

internal val DarkColors = darkColorScheme(
    primary = Color(0xFFCBBFF5),
    onPrimary = Color(0xFF241A50),
    primaryContainer = Color(0xFF3A2E73),
    onPrimaryContainer = Color(0xFFE8E2FF),
    secondary = Color(0xFFE9AE93),
    onSecondary = Color(0xFF42200F),
    secondaryContainer = Color(0xFF5C3521),
    onSecondaryContainer = Color(0xFFFBDDD0),
    tertiary = Color(0xFFA8D3C0),
    onTertiary = Color(0xFF10331F),
    tertiaryContainer = Color(0xFF2B4C3B),
    onTertiaryContainer = Color(0xFFD5EDE1),
    background = Color(0xFF16141C),
    onBackground = Color(0xFFEAE6F0),
    surface = Color(0xFF16141C),
    onSurface = Color(0xFFEAE6F0),
    surfaceVariant = Color(0xFF2C2839),
    onSurfaceVariant = Color(0xFFBDB8CB),
    surfaceContainerLowest = Color(0xFF120F18),
    surfaceContainerLow = Color(0xFF1C1924),
    surfaceContainer = Color(0xFF201D28),
    surfaceContainerHigh = Color(0xFF2A2634),
    surfaceContainerHighest = Color(0xFF35303F),
    outline = Color(0xFF948EA6),
    outlineVariant = Color(0xFF3D3749),
    error = Color(0xFFF2B8B5),
    onError = Color(0xFF601410),
    errorContainer = Color(0xFF8C1D18),
    onErrorContainer = Color(0xFFF9DEDC),
)
