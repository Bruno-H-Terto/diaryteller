package com.callme.ai.core.ui

import androidx.compose.runtime.compositionLocalOf
import androidx.compose.animation.core.CubicBezierEasing
import androidx.compose.animation.core.Easing

/**
 * Motion budget of the product: short dissolves between states, a slightly
 * slower panel reveal and no continuous decoration. Screens must check
 * [LocalReduceMotion] before animating anything that never settles.
 */
object Motion {
    const val TAP_MS = 120
    const val DISSOLVE_MS = 200
    const val PANEL_MS = 240

    /** Single easing curve shared by every transition. */
    val Ease: Easing = CubicBezierEasing(0.2f, 0f, 0f, 1f)
}

/** True when the user asked the system to reduce animations. */
val LocalReduceMotion = compositionLocalOf { false }
