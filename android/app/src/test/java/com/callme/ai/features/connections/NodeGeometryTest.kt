package com.callme.ai.features.connections

import com.callme.ai.features.connections.domain.NodeGeometry
import com.google.common.truth.Truth.assertThat
import org.junit.Test

class NodeGeometryTest {

    @Test
    fun `peripheral nodes never reach the centre size`() {
        val counts = listOf(0, 1, 2, 3, 4, 6, 7, 11, 12, 40, 500)
        counts.forEach { count ->
            val size = NodeGeometry.diameter(count)
            assertThat(size).isAtLeast(NodeGeometry.MIN)
            assertThat(size).isLessThan(NodeGeometry.CENTER)
            assertThat(size).isAtMost(NodeGeometry.MAX)
        }
    }

    @Test
    fun `growth is gradual and never proportional to the raw count`() {
        val sizes = listOf(1, 2, 5, 8, 20, 200).map { NodeGeometry.diameter(it) }

        assertThat(sizes).isInOrder()
        assertThat(NodeGeometry.diameter(1_000)).isEqualTo(NodeGeometry.diameter(20))
        assertThat(NodeGeometry.diameter(200) / NodeGeometry.diameter(1)).isLessThan(2f)
    }

    @Test
    fun `ring places every node without repeating a position`() {
        val positions = NodeGeometry.ring(7, radius = 120f)

        assertThat(positions).hasSize(7)
        assertThat(positions.toSet()).hasSize(7)
        positions.forEach { (x, y) ->
            val distance = kotlin.math.sqrt(x * x + y * y)
            assertThat(distance).isWithin(0.5f).of(120f)
        }
    }

    @Test
    fun `ring clears the centre bubble on narrow screens`() {
        val width = 280f
        val height = 230f
        val centre = NodeGeometry.centerDiameter(width, height)
        val node = NodeGeometry.diameter(3, height)
        val radius = NodeGeometry.radius(centre, height)

        assertThat(centre).isLessThan(NodeGeometry.CENTER)
        assertThat(centre).isGreaterThan(node)
        assertThat(radius - node / 2f).isAtLeast(centre / 2f - 1f)
        assertThat(radius + node / 2f).isAtMost(width / 2f)
    }
}
