package com.callme.ai.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.ChatBubbleOutline
import androidx.compose.material.icons.outlined.Hub
import androidx.compose.material.icons.outlined.MenuBook
import androidx.compose.material.icons.outlined.Tune
import androidx.compose.ui.graphics.vector.ImageVector
import com.callme.ai.R

/** One bottom bar destination. */
data class Tab(val route: String, val label: Int, val icon: ImageVector)

/** The four root destinations, in bar order. */
val tabs = listOf(
    Tab(Destinations.DIARY, R.string.tab_diary, Icons.Outlined.MenuBook),
    Tab(Destinations.CONNECTIONS, R.string.tab_connections, Icons.Outlined.Hub),
    Tab(Destinations.CONVERSATIONS, R.string.tab_conversations, Icons.Outlined.ChatBubbleOutline),
    Tab(Destinations.SETTINGS, R.string.tab_settings, Icons.Outlined.Tune),
)
