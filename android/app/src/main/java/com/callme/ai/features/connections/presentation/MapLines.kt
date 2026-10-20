package com.callme.ai.features.connections.presentation

import androidx.compose.foundation.Canvas
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.dp

/** Draws the quiet dotted field and organic owner-to-connection paths. */
@Composable
internal fun MapLines(
    slots: List<Pair<Float, Float>>,
    verticalShift: Float,
    lineColor: Color,
    dotColor: Color,
    modifier: Modifier = Modifier,
) {
    Canvas(modifier) {
        val step = 18.dp.toPx()
        var x = step / 2f
        while (x < size.width) {
            var y = step / 2f
            while (y < size.height) {
                drawCircle(dotColor, radius = 0.8.dp.toPx(), center = Offset(x, y))
                y += step
            }
            x += step
        }
        val centre = Offset(size.width / 2f, size.height / 2f + verticalShift)
        slots.forEachIndexed { index, (slotX, slotY) ->
            val end = Offset(centre.x + slotX, centre.y + slotY)
            val bend = if (index % 2 == 0) -1f else 1f
            val path = Path().apply {
                moveTo(centre.x, centre.y)
                cubicTo(
                    centre.x + slotX * 0.24f + 12.dp.toPx() * bend,
                    centre.y + slotY * 0.32f,
                    centre.x + slotX * 0.72f - 8.dp.toPx() * bend,
                    centre.y + slotY * 0.72f,
                    end.x,
                    end.y,
                )
            }
            drawPath(
                path = path,
                color = lineColor,
                style = Stroke(width = 1.7.dp.toPx(), cap = StrokeCap.Round),
            )
            drawCircle(lineColor, radius = 2.5.dp.toPx(), center = end)
        }
    }
}
