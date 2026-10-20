package com.callme.ai.features.connections.presentation

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CenterFocusStrong
import androidx.compose.material.icons.outlined.Info
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.withFrameNanos
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.callme.ai.R
import com.callme.ai.core.model.AvatarStyle
import com.callme.ai.core.ui.EntityAvatar
import com.callme.ai.core.ui.LocalReduceMotion
import com.callme.ai.features.connections.domain.ConnectionNode
import com.callme.ai.features.connections.domain.NodeGeometry
import kotlin.math.roundToInt
import kotlin.math.sin

/**
 * Personal map: the owner stays in the centre, confirmed connections sit on a
 * ring and everything else is grouped. Frequency only changes size in bands, so
 * no peripheral bubble can ever reach the centre.
 */
@Composable
fun ConnectionMap(
    nodes: List<ConnectionNode>,
    selectedId: String?,
    onSelect: (ConnectionNode) -> Unit,
    onOpenGroup: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val reduceMotion = LocalReduceMotion.current
    var scale by remember { mutableFloatStateOf(1f) }
    var pan by remember { mutableStateOf(Offset.Zero) }
    var interacting by remember { mutableStateOf(false) }

    Box(
        modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.background)
            .pointerInput(Unit) {
                detectTransformGestures { _, delta, zoom, _ ->
                    interacting = true
                    scale = (scale * zoom).coerceIn(1f, 2.2f)
                    pan += delta
                }
            },
    ) {
        BoxWithConstraints(Modifier.fillMaxSize()) {
            LaunchedEffect(interacting) {
                if (interacting) {
                    kotlinx.coroutines.delay(900)
                    interacting = false
                }
            }
            val animate = !reduceMotion && !interacting && selectedId == null
            val seconds = rememberFloatTicker(animate)
            val density = LocalDensity.current
            val widthPx = with(density) { maxWidth.toPx() }
            val heightPx = with(density) { maxHeight.toPx() }
            val widthDp = this.maxWidth.value
            val heightDp = this.maxHeight.value
            val centerDp = NodeGeometry.centerDiameter(widthDp, heightDp)
            val groupSize = (nodes.size - shownCount(nodes.size)).coerceAtLeast(0)
            val shown = nodes.take(shownCount(nodes.size))
            val slotCount = shown.size + if (groupSize > 0) 1 else 0
            val radiusX = widthPx * 0.44f
            val radiusY = minOf(heightPx * 0.4f, heightPx / 2f - with(density) { 64.dp.toPx() })
            val slots = NodeGeometry.constellation(slotCount, radiusX, radiusY)
            val labelRoom = with(density) { 10.dp.toPx() }
            val connectionColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.58f)
            val dotColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.12f)

            Box(
                Modifier.fillMaxSize().graphicsLayer {
                    scaleX = scale
                    scaleY = scale
                    translationX = pan.x
                    translationY = pan.y
                },
            ) {
                MapLines(slots, -labelRoom, connectionColor, dotColor, Modifier.fillMaxSize())
                CenterBubble(centerDp.dp, Modifier.align(Alignment.Center).offset { IntOffset(0, -labelRoom.roundToInt()) })
                shown.forEachIndexed { index, node ->
                    val (x, y) = node.pin?.let { it.x * radiusX to it.y * radiusY }
                        ?: slots.getOrElse(index) { 0f to 0f }
                    val diameter = with(density) {
                        NodeGeometry.diameter(node.recordCount, heightDp).dp.toPx()
                    }
                    val amplitude = with(density) { 3.dp.toPx() }
                    MapNode(
                        node = node,
                        diameter = diameter,
                        selected = node.id == selectedId,
                        dimmed = selectedId != null && node.id != selectedId,
                        modifier = Modifier
                            .offset {
                                IntOffset(
                                    (widthPx / 2f + x - with(density) { 46.dp.toPx() }).roundToInt(),
                                    (heightPx / 2f + y - diameter / 2f - labelRoom).roundToInt(),
                                )
                            }
                            .graphicsLayer {
                                translationY = sin(seconds * 1.1f + index) * amplitude
                            }
                            .clickable { onSelect(node) },
                    )
                }
                if (groupSize > 0) {
                    val (x, y) = slots.lastOrNull() ?: (0f to 0f)
                    val groupDiameter = with(density) { (NodeGeometry.MAX * NodeGeometry.fit(heightDp)).dp.toPx() }
                    MapGroupBubble(
                        count = groupSize,
                        modifier = Modifier
                            .offset {
                                IntOffset(
                                    (widthPx / 2f + x - groupDiameter / 2f).roundToInt(),
                                    (heightPx / 2f + y - groupDiameter / 2f - labelRoom).roundToInt(),
                                )
                            }
                            .clickable(onClick = onOpenGroup),
                    )
                }
            }
            if (scale > 1f || pan != Offset.Zero) {
                RecenterButton(Modifier.align(Alignment.BottomEnd).padding(8.dp)) {
                    scale = 1f
                    pan = Offset.Zero
                }
            }
        }
    }
}
