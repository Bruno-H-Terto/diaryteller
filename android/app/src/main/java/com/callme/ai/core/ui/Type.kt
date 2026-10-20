package com.callme.ai.core.ui

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontVariation
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import com.callme.ai.R

@OptIn(androidx.compose.ui.text.ExperimentalTextApi::class)
private fun rounded(weight: Int) = Font(
    resId = R.font.nunito,
    weight = FontWeight(weight),
    variationSettings = FontVariation.Settings(FontVariation.weight(weight)),
)

@OptIn(androidx.compose.ui.text.ExperimentalTextApi::class)
private fun reading(weight: Int) = Font(
    resId = R.font.nunito_sans,
    weight = FontWeight(weight),
    variationSettings = FontVariation.Settings(FontVariation.weight(weight)),
)

/** Headings use rounded Nunito; reading text uses the wider Nunito Sans. */
internal val Nunito = FontFamily(rounded(400), rounded(600), rounded(700), rounded(800))
internal val NunitoSans = FontFamily(reading(400), reading(600), reading(700))

private fun heading(size: Int, lineHeight: Int, weight: Int = 700, tracking: Double = -0.4) =
    TextStyle(
        fontFamily = Nunito,
        fontWeight = FontWeight(weight),
        fontSize = size.sp,
        lineHeight = lineHeight.sp,
        letterSpacing = tracking.sp,
    )

private fun body(size: Int, lineHeight: Int, weight: Int = 400, tracking: Double = 0.0) =
    TextStyle(
        fontFamily = NunitoSans,
        fontWeight = FontWeight(weight),
        fontSize = size.sp,
        lineHeight = lineHeight.sp,
        letterSpacing = tracking.sp,
    )

/** Type scale of the redesign: large friendly headings and calm reading text. */
internal val CallMeTypography = Typography(
    displaySmall = heading(36, 42, 800, -0.8),
    headlineLarge = heading(30, 38, 800, -0.6),
    headlineMedium = heading(26, 34, 700, -0.4),
    headlineSmall = heading(22, 30, 700, -0.2),
    titleLarge = heading(20, 28, 700, 0.0),
    titleMedium = heading(17, 24, 700, 0.0),
    titleSmall = heading(15, 22, 700, 0.0),
    bodyLarge = body(16, 26),
    bodyMedium = body(15, 24),
    bodySmall = body(13, 20),
    labelLarge = body(15, 20, 600),
    labelMedium = body(12, 16, 600, 0.3),
    labelSmall = body(11, 16, 700, 0.8),
)
