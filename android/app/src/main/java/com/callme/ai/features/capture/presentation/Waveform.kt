package com.callme.ai.features.capture.presentation

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.unit.dp
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.sin

/** Decorative waveform: bars breathe while recording and rest when idle. */
@Composable
internal fun Waveform(active: Boolean) {
    val transition = rememberInfiniteTransition(label = "waveform")
    val phase by transition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(durationMillis = 1600, easing = LinearEasing)),
        label = "phase",
    )
    val barColor = MaterialTheme.colorScheme.primary
    Canvas(
        Modifier
            .fillMaxWidth()
            .height(150.dp)
            .clip(RoundedCornerShape(44.dp))
            .background(MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.55f)),
    ) {
        val count = 46
        val inset = size.width * 0.06f
        val usable = size.width - inset * 2
        val gap = usable / count * 0.42f
        val barWidth = (usable - gap * (count - 1)) / count
        val radius = CornerRadius(barWidth / 2f, barWidth / 2f)
        repeat(count) { index ->
            val wave = abs(sin(index * 0.55f + phase * 6.2832f)) * 0.7f + abs(cos(index * 0.23f)) * 0.3f
            val factor = if (active) 0.18f + wave * 0.82f else 0.16f + wave * 0.18f
            val height = size.height * factor * 0.86f
            val x = inset + index * (barWidth + gap)
            drawRoundRect(
                color = barColor,
                topLeft = Offset(x, (size.height - height) / 2f),
                size = Size(barWidth, height),
                cornerRadius = radius,
            )
        }
    }
}
