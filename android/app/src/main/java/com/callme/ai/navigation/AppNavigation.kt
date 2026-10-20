package com.callme.ai.navigation

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.isImeVisible
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.ChatBubbleOutline
import androidx.compose.material.icons.outlined.MenuBook
import androidx.compose.material.icons.outlined.Hub
import androidx.compose.material.icons.outlined.Tune
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewmodel.compose.viewModel
import com.callme.ai.navigation.factory
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.callme.ai.R
import com.callme.ai.features.capture.application.CaptureService
import com.callme.ai.features.capture.domain.CaptureMode
import com.callme.ai.features.capture.presentation.CaptureScreen
import com.callme.ai.features.capture.presentation.CaptureViewModel
import com.callme.ai.features.conversations.application.ConversationRepository
import com.callme.ai.features.conversations.domain.SelectableRecord
import com.callme.ai.features.conversations.presentation.ConversationScreen
import com.callme.ai.features.capture.application.DictationEngine
import com.callme.ai.features.conversations.application.DiaryMutator
import com.callme.ai.features.conversations.application.ReplySpeaker
import com.callme.ai.features.conversations.presentation.ConversationViewModel
import com.callme.ai.features.connections.application.ConnectionsRepository
import com.callme.ai.features.connections.presentation.ConnectionsScreen
import com.callme.ai.features.connections.presentation.ConnectionsViewModel
import com.callme.ai.features.entities.application.EntitiesRepository
import com.callme.ai.features.entities.domain.EntityType
import com.callme.ai.features.entities.presentation.AvatarEditorScreen
import com.callme.ai.features.entities.presentation.AvatarEditorViewModel
import com.callme.ai.features.records.application.RecordsRepository
import com.callme.ai.features.records.presentation.DiaryScreen
import com.callme.ai.features.records.presentation.EditorScreen
import com.callme.ai.features.records.presentation.EditorViewModel
import com.callme.ai.features.records.presentation.RecordsViewModel
import com.callme.ai.features.records.presentation.VersionsScreen
import com.callme.ai.core.database.SampleDiary

/** Root scaffold: tab bar for the three destinations, full-screen routes above it. */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun MainScaffold(
    recordsRepository: RecordsRepository,
    captureService: CaptureService,
    conversationRepository: ConversationRepository,
    diaryMutator: DiaryMutator,
    dictation: DictationEngine,
    replySpeaker: () -> ReplySpeaker,
    connectionsRepository: ConnectionsRepository,
    entitiesRepository: EntitiesRepository,
    sampleDiary: SampleDiary,
    email: String,
    onSignOut: () -> Unit,
    navController: NavHostController = rememberNavController(),
) {
    val entry by navController.currentBackStackEntryAsState()
    val route = entry?.destination?.route
    val showBar = tabs.any { it.route == route } && !WindowInsets.isImeVisible
    Scaffold(
        modifier = Modifier.imePadding(),
        bottomBar = {
            if (showBar) {
                Column {
                    HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
                    NavigationBar(
                        containerColor = MaterialTheme.colorScheme.surface,
                        tonalElevation = 0.dp,
                    ) {
                        tabs.forEach { tab ->
                            NavigationBarItem(
                                selected = route == tab.route,
                                onClick = { navController.navigateToTab(tab.route) },
                                icon = { Icon(tab.icon, contentDescription = null) },
                                label = {
                                    Text(
                                        stringResource(tab.label),
                                        maxLines = 1,
                                        overflow = TextOverflow.Ellipsis,
                                        style = MaterialTheme.typography.labelSmall,
                                    )
                                },
                                colors = NavigationBarItemDefaults.colors(
                                    selectedIconColor = MaterialTheme.colorScheme.primary,
                                    selectedTextColor = MaterialTheme.colorScheme.onSurface,
                                    indicatorColor = MaterialTheme.colorScheme.primaryContainer,
                                    unselectedIconColor = MaterialTheme.colorScheme.onSurfaceVariant,
                                    unselectedTextColor = MaterialTheme.colorScheme.onSurfaceVariant,
                                ),
                            )
                        }
                    }
                }
            }
        },
    ) { padding ->
        NavHost(
            navController = navController,
            startDestination = Destinations.DIARY,
            modifier = Modifier.padding(padding),
        ) {
            composable(Destinations.DIARY) {
                val vm: RecordsViewModel = viewModel(factory = factory { RecordsViewModel(recordsRepository) })
                DiaryScreen(
                    viewModel = vm,
                    onOpen = { navController.navigate(Destinations.editor(it)) },
                    onCapture = { navController.navigate(Destinations.capture(it.name.lowercase())) },
                )
            }
            conversationRoute(
                recordsRepository = recordsRepository,
                conversationRepository = conversationRepository,
                diaryMutator = diaryMutator,
                dictation = dictation,
                replySpeaker = replySpeaker,
            )
            detailRoutes(navController, connectionsRepository, entitiesRepository)
            settingsRoutes(navController, sampleDiary, email, onSignOut)
            composable(Destinations.EDITOR) { backStack ->
                val recordId = backStack.arguments?.getString("recordId").orEmpty()
                val vm: EditorViewModel = viewModel(
                    key = "editor-$recordId",
                    factory = factory { EditorViewModel(recordsRepository, recordId) },
                )
                EditorScreen(
                    viewModel = vm,
                    onClose = { navController.popBackStack() },
                    onVersions = { navController.navigate(Destinations.versions(recordId)) },
                )
            }
            composable(Destinations.CAPTURE) { backStack ->
                val mode = if (backStack.arguments?.getString("mode") == "recording") {
                    CaptureMode.RECORDING
                } else {
                    CaptureMode.DICTATION
                }
                val vm: CaptureViewModel = viewModel(
                    key = "capture-${mode.name}",
                    factory = factory { CaptureViewModel(captureService, recordsRepository) },
                )
                CaptureScreen(
                    mode = mode,
                    viewModel = vm,
                    onSaved = { recordId ->
                        navController.popBackStack()
                        navController.navigate(Destinations.editor(recordId))
                    },
                    onClose = { navController.popBackStack() },
                )
            }
            composable(Destinations.VERSIONS) { backStack ->
                val recordId = backStack.arguments?.getString("recordId").orEmpty()
                val vm: EditorViewModel = viewModel(
                    key = "editor-$recordId",
                    factory = factory { EditorViewModel(recordsRepository, recordId) },
                )
                VersionsScreen(vm, onClose = { navController.popBackStack() })
            }
        }
    }
}

private fun NavHostController.navigateToTab(route: String) {
    navigate(route) {
        popUpTo(Destinations.DIARY) { saveState = true }
        launchSingleTop = true
        restoreState = true
    }
}
