package com.callme.ai.features.connections.presentation

import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.withFrameNanos
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.callme.ai.R
import com.callme.ai.core.model.AvatarStyle
import com.callme.ai.core.ui.EntityAvatar
import com.callme.ai.features.connections.domain.ConnectionNode
import com.callme.ai.features.connections.domain.NodeGeometry

/** Drives the slow vertical drift. No frames are produced when motion is paused. */
@Composable
internal fun rememberFloatTicker(active: Boolean): Float {
    var seconds by remember { mutableFloatStateOf(0f) }
    LaunchedEffect(active) {
        if (!active) return@LaunchedEffect
        val start = withFrameNanos { it }
        var frame = 0
        while (true) {
            withFrameNanos { now ->
                // The drift is slow; a fifth of the frames keeps the GPU idle.
                if (frame++ % 5 == 0) seconds = (now - start) / 1_000_000_000f
            }
        }
    }
    return seconds
}

/** How many connections get their own bubble before the rest are grouped. */
internal fun shownCount(total: Int): Int =
    if (total <= MapVisibility.INDIVIDUAL) total else MapVisibility.INDIVIDUAL_WITH_GROUP

@Composable
internal fun CenterBubble(records: Int, size: Dp, modifier: Modifier = Modifier) {
    Column(modifier, horizontalAlignment = Alignment.CenterHorizontally) {
        Surface(shape = CircleShape, color = MaterialTheme.colorScheme.primary, modifier = Modifier.size(size)) {
            Box(contentAlignment = Alignment.Center) {
                EntityAvatar(AvatarStyle("p2", 0xFFEAE5F6), size = size * 0.8f)
            }
        }
        Text(
            stringResource(R.string.connections_you),
            style = MaterialTheme.typography.labelMedium,
            modifier = Modifier.padding(top = 4.dp),
        )
    }
}

@Composable
internal fun MapNode(
    node: ConnectionNode,
    diameter: Float,
    labelAbove: Boolean,
    selected: Boolean,
    dimmed: Boolean,
    modifier: Modifier = Modifier,
) {
    val size = with(LocalDensity.current) { diameter.toDp() }
    Column(
        modifier = modifier.widthIn(min = 72.dp).graphicsLayer { alpha = if (dimmed) 0.45f else 1f },
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        if (labelAbove) {
            Text(
                node.name,
                style = MaterialTheme.typography.labelSmall,
                maxLines = 1,
                modifier = Modifier.padding(bottom = 4.dp),
            )
        }
        Box(contentAlignment = Alignment.Center) {
            Surface(
                shape = CircleShape,
                color = MaterialTheme.colorScheme.primaryContainer,
                shadowElevation = if (selected) 4.dp else 1.dp,
                modifier = Modifier.size(size).padding(3.dp),
            ) {
                EntityAvatar(node.avatar, size = size - 6.dp)
            }
            if (selected) {
                Box(
                    Modifier
                        .size(size + 6.dp)
                        .border(2.dp, MaterialTheme.colorScheme.primary, CircleShape),
                )
            }
        }
        if (!labelAbove) {
            Text(
                node.name,
                style = MaterialTheme.typography.labelSmall,
                maxLines = 1,
                modifier = Modifier.padding(top = 4.dp),
            )
        }
    }
}

@Composable
internal fun MapGroupBubble(count: Int, modifier: Modifier = Modifier) {
    Column(modifier, horizontalAlignment = Alignment.CenterHorizontally) {
        Surface(
            shape = CircleShape,
            color = MaterialTheme.colorScheme.primaryContainer,
            modifier = Modifier.size(NodeGeometry.MAX.dp),
        ) {
            Box(contentAlignment = Alignment.Center) {
                Text("+$count", style = MaterialTheme.typography.titleMedium)
            }
        }
        Text(
            stringResource(R.string.connections_group),
            style = MaterialTheme.typography.labelSmall,
            modifier = Modifier.padding(top = 4.dp),
        )
    }
}
