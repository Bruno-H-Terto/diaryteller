package com.callme.ai.core.ui

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import com.callme.ai.R

private val Poppins = FontFamily(
    Font(R.font.poppins_regular, FontWeight.Normal),
    Font(R.font.poppins_medium, FontWeight.Medium),
    Font(R.font.poppins_semibold, FontWeight.SemiBold),
    Font(R.font.poppins_bold, FontWeight.Bold),
)

private fun style(
    size: Int,
    lineHeight: Int,
    weight: FontWeight = FontWeight.Normal,
    tracking: Double = 0.0,
) = TextStyle(
    fontFamily = Poppins,
    fontWeight = weight,
    fontSize = size.sp,
    lineHeight = lineHeight.sp,
    letterSpacing = tracking.sp,
)

/** Type scale of the redesign: geometric sans, tight headlines, calm body text. */
internal val CallMeTypography = Typography(
    displaySmall = style(38, 44, FontWeight.SemiBold, -0.8),
    headlineLarge = style(32, 40, FontWeight.SemiBold, -0.6),
    headlineMedium = style(28, 36, FontWeight.SemiBold, -0.4),
    headlineSmall = style(24, 32, FontWeight.SemiBold, -0.2),
    titleLarge = style(20, 28, FontWeight.Medium),
    titleMedium = style(18, 26, FontWeight.Medium),
    titleSmall = style(15, 22, FontWeight.Medium),
    bodyLarge = style(16, 26),
    bodyMedium = style(15, 24),
    bodySmall = style(13, 20),
    labelLarge = style(15, 20, FontWeight.Medium),
    labelMedium = style(12, 16, FontWeight.Medium, 0.4),
    labelSmall = style(11, 16, FontWeight.Medium, 0.8),
)
