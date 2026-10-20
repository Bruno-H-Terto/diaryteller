package com.callme.ai.core.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.callme.ai.core.model.AvatarStyle

/** Rounded cartoon avatar drawn in code: no third-party assets, consistent everywhere. */
@Composable
fun EntityAvatar(
    style: AvatarStyle,
    size: Dp = 48.dp,
    modifier: Modifier = Modifier,
) {
    Canvas(modifier.size(size).clip(CircleShape)) {
        drawRect(Color(style.background))
        val unit = this.size.minDimension / 100f
        fun p(x: Float, y: Float) = Offset(x * unit, y * unit)
        when (style.model.firstOrNull()) {
            'a' -> drawAnimal(style, ::p, unit)
            'l' -> drawPlace(style, ::p, unit)
            'e' -> drawEvent(style, ::p)
            else -> drawPerson(style, ::p, unit)
        }
    }
}

private const val SkinArgb = 0xFFE8C39EL
private const val HairArgb = 0xFF3B2E2AL
private const val ClothingArgb = 0xFF51438FL
private val Ink = Color(0xFF2B2938)

private fun DrawScope.drawPerson(
    style: AvatarStyle,
    p: (Float, Float) -> Offset,
    unit: Float,
) {
    val skin = Color(style.skin ?: SkinArgb)
    val hair = Color(style.hair ?: HairArgb)
    val clothing = Color(style.clothing ?: ClothingArgb)
    drawOval(clothing, p(27f, 66f), Size(46 * unit, 44 * unit))
    when (style.model) {
        "p2" -> {
            drawOval(hair, p(24f, 18f), Size(52 * unit, 56 * unit))
            drawOval(skin, p(31f, 28f), Size(38 * unit, 42 * unit))
        }
        "p3" -> {
            for ((x, y) in listOf(32f to 26f, 50f to 20f, 68f to 26f, 26f to 40f, 74f to 40f)) {
                drawCircle(hair, 11 * unit, p(x, y))
            }
            drawOval(skin, p(32f, 30f), Size(36 * unit, 38 * unit))
        }
        "p4" -> {
            drawOval(hair, p(28f, 22f), Size(44 * unit, 26 * unit))
            drawOval(skin, p(33f, 30f), Size(34 * unit, 38 * unit))
        }
        else -> {
            drawOval(hair, p(26f, 20f), Size(48 * unit, 44 * unit))
            drawOval(skin, p(33f, 28f), Size(34 * unit, 40 * unit))
            drawOval(hair, p(26f, 18f), Size(48 * unit, 18 * unit))
        }
    }
    drawCircle(Ink, 1.7f * unit, p(43f, 46f))
    drawCircle(Ink, 1.7f * unit, p(57f, 46f))
    val smile = Path().apply {
        moveTo(p(45f, 53f).x, p(45f, 53f).y)
        quadraticBezierTo(p(50f, 57f).x, p(50f, 57f).y, p(55f, 53f).x, p(55f, 53f).y)
    }
    drawPath(smile, Ink, style = androidx.compose.ui.graphics.drawscope.Stroke(width = 1.6f * unit))
}

private fun DrawScope.drawAnimal(
    style: AvatarStyle,
    p: (Float, Float) -> Offset,
    unit: Float,
) {
    val fur = Color(style.skin ?: SkinArgb)
    val accent = Color(style.hair ?: HairArgb)
    if (style.model == "a2") {
        drawPath(Path().apply {
            moveTo(p(30f, 30f).x, p(30f, 30f).y)
            lineTo(p(38f, 20f).x, p(38f, 20f).y)
            lineTo(p(44f, 32f).x, p(44f, 32f).y)
            close()
        }, accent)
        drawPath(Path().apply {
            moveTo(p(70f, 30f).x, p(70f, 30f).y)
            lineTo(p(62f, 20f).x, p(62f, 20f).y)
            lineTo(p(56f, 32f).x, p(56f, 32f).y)
            close()
        }, accent)
    } else {
        drawOval(accent, p(24f, 30f), Size(20 * unit, 26 * unit))
        drawOval(accent, p(56f, 30f), Size(20 * unit, 26 * unit))
    }
    drawOval(fur, p(28f, 28f), Size(44 * unit, 44 * unit))
    drawOval(accent, p(41f, 50f), Size(18 * unit, 14 * unit))
    drawCircle(Ink, 1.8f * unit, p(42f, 44f))
    drawCircle(Ink, 1.8f * unit, p(58f, 44f))
    drawCircle(Color(0xFF3B2E2A), 2.4f * unit, p(50f, 54f))
}

private fun DrawScope.drawPlace(
    style: AvatarStyle,
    p: (Float, Float) -> Offset,
    unit: Float,
) {
    val roof = Color(style.hair ?: ClothingArgb)
    val body = Color(style.clothing ?: 0xFFE0B48Aff)
    if (style.model == "l2") {
        drawRect(Color(0xFF8A6A4B), p(46f, 58f), Size(8 * unit, 30 * unit))
        drawCircle(Color(0xFF6E9E72), 18 * unit, p(50f, 44f))
        drawCircle(Color(0xFF7FAE7F), 13 * unit, p(32f, 52f))
        drawCircle(Color(0xFF7FAE7F), 13 * unit, p(68f, 52f))
    } else {
        drawPath(Path().apply {
            moveTo(p(18f, 50f).x, p(18f, 50f).y)
            lineTo(p(50f, 24f).x, p(50f, 24f).y)
            lineTo(p(82f, 50f).x, p(82f, 50f).y)
            close()
        }, roof)
        drawRect(body, p(27f, 50f), Size(46 * unit, 34 * unit))
        drawRect(roof, p(43f, 62f), Size(14 * unit, 22 * unit))
    }
}

private fun DrawScope.drawEvent(style: AvatarStyle, p: (Float, Float) -> Offset) {
    val page = Color(style.clothing ?: 0xFFFFFDF9)
    val header = Color(style.hair ?: ClothingArgb)
    drawRect(page, p(22f, 20f), Size(56f * 1f, 62f * 1f))
    drawRect(header, p(22f, 20f), Size(56f, 14f))
    drawCircle(Color(0xFFB86443), 5f, p(38f, 52f))
    drawCircle(header, 5f, p(58f, 52f))
    drawRect(header, p(34f, 64f), Size(32f, 4f))
}
