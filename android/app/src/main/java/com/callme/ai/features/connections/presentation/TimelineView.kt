package com.callme.ai.features.connections.presentation

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material.icons.filled.ExpandMore
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.pluralStringResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.callme.ai.R
import com.callme.ai.core.ui.PillButton
import com.callme.ai.core.ui.SectionLabel
import com.callme.ai.features.connections.domain.TimelineDay
import com.callme.ai.features.connections.domain.TimelineMonth

/**
 * Timeline: months, collapsible days and event cards. Expansion lives in the
 * view model and the list state is remembered, so returning from a detail keeps
 * both position and open days.
 */
@Composable
fun TimelineView(
    months: List<TimelineMonth>,
    expanded: Set<String>,
    onToggleDay: (String) -> Unit,
    onOpenEvent: (String) -> Unit,
    onOpenRecord: (String) -> Unit,
    canLoadMore: Boolean,
    onLoadMore: () -> Unit,
    reviewCount: Int,
    onReview: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val listState = rememberLazyListState()
    LazyColumn(
        state = listState,
        modifier = modifier.fillMaxWidth(),
        contentPadding = PaddingValues(bottom = 24.dp),
    ) {
        if (months.isEmpty()) {
            item {
                Text(
                    stringResource(R.string.timeline_empty),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(24.dp),
                )
            }
        }
        months.forEach { month ->
            item(key = "month-${month.key}") { MonthHeader(month) }
            month.days.forEach { day ->
                if (day.date == null) {
                    items(day.events, key = { "event-${it.id}" }) { event ->
                        EventCard(
                            event = event,
                            onOpen = { onOpenEvent(event.id) },
                            onOpenRecord = onOpenRecord,
                            modifier = Modifier.padding(horizontal = 20.dp, vertical = 6.dp),
                        )
                    }
                } else {
                    item(key = "day-${month.key}-${day.key}") {
                        DayRow(
                            day = day,
                            open = day.key in expanded,
                            onToggle = { onToggleDay(day.key) },
                        )
                    }
                    if (day.key in expanded) {
                        items(day.events, key = { "event-${it.id}" }) { event ->
                            EventCard(
                                event = event,
                                onOpen = { onOpenEvent(event.id) },
                                onOpenRecord = onOpenRecord,
                                modifier = Modifier.padding(horizontal = 20.dp, vertical = 6.dp),
                            )
                        }
                    }
                }
            }
        }
        if (canLoadMore) {
            item {
                PillButton(
                    label = stringResource(R.string.timeline_load_more),
                    onClick = onLoadMore,
                    tonal = true,
                    modifier = Modifier.fillMaxWidth().padding(20.dp),
                )
            }
        }
        if (reviewCount > 0) {
            item {
                PillButton(
                    label = stringResource(R.string.timeline_review_events, reviewCount),
                    onClick = onReview,
                    modifier = Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 8.dp),
                )
            }
        }
    }
}

@Composable
private fun MonthHeader(month: TimelineMonth) {
    Column(Modifier.padding(start = 20.dp, end = 20.dp, top = 20.dp, bottom = 4.dp)) {
        Text(month.label, style = MaterialTheme.typography.titleLarge)
        Text(
            pluralStringResource(R.plurals.timeline_month_count, month.eventCount, month.eventCount),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
private fun DayRow(day: TimelineDay, open: Boolean, onToggle: () -> Unit) {
    Row(
        Modifier.fillMaxWidth().clickable(onClick = onToggle).padding(horizontal = 20.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(Modifier.weight(1f)) {
            Text(day.label, style = MaterialTheme.typography.titleSmall)
            Text(
                pluralStringResource(R.plurals.timeline_day_count, day.events.size, day.events.size),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        Icon(
            if (open) Icons.Filled.ExpandMore else Icons.AutoMirrored.Filled.KeyboardArrowRight,
            contentDescription = stringResource(
                if (open) R.string.timeline_collapse else R.string.timeline_expand,
            ),
            tint = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
    HorizontalDivider(
        Modifier.padding(horizontal = 20.dp),
        color = MaterialTheme.colorScheme.outlineVariant,
    )
}
