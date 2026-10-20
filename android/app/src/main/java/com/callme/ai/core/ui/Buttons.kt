package com.callme.ai.core.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp

/** Primary (filled) or tonal (lavender) pill action. */
@Composable
fun PillButton(
    label: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    tonal: Boolean = false,
) {
    val colors = MaterialTheme.colorScheme
    Surface(
        onClick = onClick,
        enabled = enabled,
        shape = CircleShape,
        color = when {
            !enabled -> colors.surfaceContainerHighest
            tonal -> colors.primaryContainer
            else -> colors.primary
        },
        contentColor = when {
            !enabled -> colors.onSurfaceVariant
            tonal -> colors.onPrimaryContainer
            else -> colors.onPrimary
        },
        modifier = modifier.height(50.dp),
    ) {
        Box(contentAlignment = Alignment.Center, modifier = Modifier.padding(horizontal = 22.dp)) {
            Text(label, style = MaterialTheme.typography.labelLarge, textAlign = TextAlign.Center)
        }
    }
}

/** Round icon action with a caption, used by the capture panel. */
@Composable
fun CircleAction(
    icon: ImageVector,
    label: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    highlighted: Boolean = false,
) {
    val colors = MaterialTheme.colorScheme
    Column(
        modifier = modifier.clickable(enabled = enabled, onClick = onClick),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Box(
            modifier = Modifier
                .size(if (highlighted) 76.dp else 56.dp)
                .background(
                    if (highlighted) colors.primary else colors.primaryContainer,
                    CircleShape,
                ),
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                icon,
                contentDescription = label,
                tint = if (highlighted) colors.onPrimary else colors.primary,
                modifier = Modifier.size(if (highlighted) 30.dp else 22.dp),
            )
        }
        Text(
            label,
            style = MaterialTheme.typography.bodySmall,
            color = if (enabled) colors.onSurface else colors.onSurfaceVariant.copy(alpha = 0.5f),
        )
    }
}

/** Pill used for filters and chips; selected state fills with lavender. */
@Composable
fun ChoicePill(
    label: String,
    selected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val colors = MaterialTheme.colorScheme
    Surface(
        onClick = onClick,
        shape = CircleShape,
        color = if (selected) colors.primaryContainer else Color.Transparent,
        contentColor = if (selected) colors.onPrimaryContainer else colors.onSurfaceVariant,
        modifier = modifier,
    ) {
        Text(
            label,
            style = MaterialTheme.typography.labelLarge,
            maxLines = 1,
            modifier = Modifier.padding(horizontal = 18.dp, vertical = 10.dp),
        )
    }
}
