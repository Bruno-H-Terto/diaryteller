package com.callme.ai.features.connections.domain

import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin

/**
 * Node geometry of the connection map, expressed in dp.
 *
 * The centre has a fixed cap and is always the largest bubble. Everything else
 * grows in discrete bands, so a busy period never produces a huge circle, and no
 * peripheral node — including groups and the selected one — reaches the centre.
 */
object NodeGeometry {
    const val CENTER = 96f
    const val MIN = 46f
    const val MAX = 68f

    /** Frequency bands: 1, 2–3, 4–6, 7–11 and 12+ distinct records. */
    fun diameter(recordCount: Int, height: Float = 360f): Float {
        val count = recordCount.coerceAtLeast(1)
        val base = when {
            count <= 1 -> MIN
            count <= 3 -> MIN + 6f
            count <= 6 -> MIN + 12f
            count <= 11 -> MIN + 17f
            else -> MAX
        }
        return base * fit(height)
    }

    /** Nodes shrink a little on short screens but keep a legible minimum. */
    fun fit(height: Float): Float = (height / 360f).coerceIn(0.84f, 1f)

    /** The centre shrinks on narrow screens but stays above every other node. */
    fun centerDiameter(width: Float, height: Float): Float =
        minOf(CENTER * fit(height), width * 0.34f).coerceAtLeast(MAX * fit(height) + 14f)

    /** Ring radius that clears the centre bubble and leaves room for the label. */
    fun radius(center: Float, height: Float): Float =
        center / 2f + (MAX * fit(height)) / 2f + 16f

    /**
     * Places a small number of nodes as a calm constellation around the owner.
     * The presets avoid the rigid visual rhythm of a graph ring and reserve the
     * lower centre for a fifth node or the grouped-connections affordance.
     */
    fun constellation(count: Int, radiusX: Float, radiusY: Float): List<Pair<Float, Float>> {
        val normalized = when (count) {
            1 -> listOf(0f to -0.86f)
            2 -> listOf(-0.72f to -0.66f, 0.72f to -0.66f)
            3 -> listOf(-0.72f to -0.66f, 0.72f to -0.66f, 0f to 0.82f)
            4 -> listOf(
                -0.74f to -0.72f,
                0.74f to -0.72f,
                -0.78f to 0.58f,
                0.78f to 0.58f,
            )
            5 -> listOf(
                -0.74f to -0.78f,
                0.74f to -0.78f,
                -0.82f to 0.06f,
                0.82f to 0.06f,
                0f to 0.86f,
            )
            else -> return ring(count, minOf(radiusX, radiusY))
        }
        return normalized.map { (x, y) -> x * radiusX to y * radiusY }
    }

    /** Places [count] nodes evenly on a ring, starting at the top. */
    fun ring(count: Int, radius: Float): List<Pair<Float, Float>> {
        if (count <= 0) return emptyList()
        val step = 2 * PI / count
        val start = -PI / 2
        return (0 until count).map { index ->
            val angle = start + index * step
            (cos(angle) * radius).toFloat() to (sin(angle) * radius).toFloat()
        }
    }
}
