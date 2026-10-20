package com.callme.ai.features.connections.presentation

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.wrapContentWidth
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowLeft
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material.icons.outlined.FilterList
import androidx.compose.material.icons.outlined.Info
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.callme.ai.R
import com.callme.ai.core.ui.SegmentTabs

/**
 * Connections area: one dataset, two views. Period and filters live in the view
 * model, so switching between map and timeline never changes the selection.
 */
@Composable
fun ConnectionsScreen(
    viewModel: ConnectionsViewModel,
    onOpenEntity: (String, String) -> Unit,
    onEditEntity: (String) -> Unit,
    onOpenEvent: (String) -> Unit,
    onOpenRecord: (String) -> Unit,
    onManageEntities: () -> Unit,
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    var filtering by remember { mutableStateOf(false) }

    Column(
        Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .padding(horizontal = 20.dp),
    ) {
        ConnectionsHeader()
        SegmentTabs(
            labels = listOf(
                stringResource(R.string.connections_map),
                stringResource(R.string.connections_timeline),
            ),
            selected = if (state.mode == ConnectionsMode.MAP) 0 else 1,
            onSelect = { viewModel.setMode(if (it == 0) ConnectionsMode.MAP else ConnectionsMode.TIMELINE) },
        )
        PeriodRow(
            label = state.period.label,
            wholeHistory = state.period.month == null,
            filtering = state.type != null,
            onPrevious = viewModel::previousPeriod,
            onNext = viewModel::nextPeriod,
            onHistory = if (state.period.month == null) viewModel::useCurrentMonth else viewModel::useWholeHistory,
            onFilter = { filtering = true },
        )
        val map = state.map
        if (state.mode == ConnectionsMode.MAP) {
            MapSizeHint()
            ConnectionMap(
                nodes = map?.nodes.orEmpty(),
                records = map?.summary?.records ?: 0,
                neighbours = map?.summary?.neighbours ?: 0,
                selectedId = state.selected?.id,
                onSelect = viewModel::select,
                onOpenGroup = viewModel::openGroup,
                modifier = Modifier.weight(1f),
            )
            ReviewBar(count = state.review.size, onClick = viewModel::openReview)
            ManageRow(onClick = onManageEntities)
        } else {
            TimelineView(
                months = state.months,
                expanded = state.expandedDays,
                onToggleDay = viewModel::toggleDay,
                onOpenEvent = onOpenEvent,
                onOpenRecord = onOpenRecord,
                canLoadMore = state.canLoadMore,
                onLoadMore = viewModel::loadMore,
                reviewCount = state.review.size,
                onReview = viewModel::openReview,
                modifier = Modifier.weight(1f),
            )
        }
    }

    state.selected?.let { node ->
        NodeDetailSheet(
            node = node,
            profile = state.profile,
            periodLabel = state.period.label,
            onDismiss = { viewModel.select(null) },
            onOpenEntity = { onOpenEntity(node.id, state.period.month?.toString().orEmpty()) },
            onEditEntity = { onEditEntity(node.id) },
            onOpenEvent = onOpenEvent,
            onOpenRecord = onOpenRecord,
        )
    }
    if (state.expandedGroup) {
        GroupSheet(
            nodes = state.map?.nodes.orEmpty().drop(MapVisibility.INDIVIDUAL_WITH_GROUP),
            total = state.map?.summary?.neighbours ?: 0,
            onDismiss = viewModel::closeGroup,
            onSelect = { node ->
                viewModel.closeGroup()
                viewModel.select(node)
            },
        )
    }
    if (state.reviewing) {
        ReviewSheet(
            items = state.review,
            onDismiss = viewModel::closeReview,
            onConfirm = viewModel::confirm,
            onDiscard = viewModel::discard,
        )
    }
    if (filtering) {
        FilterSheet(
            selected = state.type,
            query = state.query,
            onQuery = viewModel::setQuery,
            onSelect = viewModel::setType,
            onDismiss = { filtering = false },
        )
    }
}

@Composable
private fun MapSizeHint() {
    Row(
        modifier = Modifier.padding(top = 10.dp, bottom = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        Icon(
            Icons.Outlined.Info,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.primary,
            modifier = Modifier.size(16.dp),
        )
        Text(
            stringResource(R.string.connections_size_rule),
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

/** Kept together with the screen so map and group sheet agree on the ring. */
object MapVisibility {
    const val INDIVIDUAL = 4
    const val INDIVIDUAL_WITH_GROUP = 4
}
