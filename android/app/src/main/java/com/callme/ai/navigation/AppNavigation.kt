package com.callme.ai.navigation

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.List
import androidx.compose.material.icons.automirrored.filled.Chat
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Timeline
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewmodel.compose.viewModel
import com.callme.ai.R
import com.callme.ai.features.records.application.RecordsRepository
import com.callme.ai.features.records.presentation.EditorScreen
import com.callme.ai.features.records.presentation.EditorViewModel
import com.callme.ai.features.records.presentation.RecordsScreen
import com.callme.ai.features.records.presentation.RecordsViewModel
import com.callme.ai.features.records.presentation.VersionsScreen
import com.callme.ai.features.settings.presentation.AccountScreen
import com.callme.ai.features.settings.presentation.PendingScreen

private data class Tab(val route: String, val label: Int, val icon: androidx.compose.ui.graphics.vector.ImageVector)

private val tabs = listOf(
    Tab(Destinations.RECORDS, R.string.tab_records, Icons.AutoMirrored.Filled.List),
    Tab(Destinations.CONVERSATION, R.string.tab_conversation, Icons.AutoMirrored.Filled.Chat),
    Tab(Destinations.TIMELINE, R.string.tab_timeline, Icons.Default.Timeline),
    Tab(Destinations.ACCOUNT, R.string.tab_account, Icons.Default.Person),
)

@Composable
fun MainScaffold(
    recordsRepository: RecordsRepository,
    email: String,
    onSignOut: () -> Unit,
    navController: NavHostController = rememberNavController(),
) {
    val entry by navController.currentBackStackEntryAsState()
    val route = entry?.destination?.route
    val showBar = tabs.any { it.route == route }
    Scaffold(
        bottomBar = {
            if (showBar) {
                NavigationBar {
                    tabs.forEach { tab ->
                        NavigationBarItem(
                            selected = route == tab.route,
                            onClick = {
                                navController.navigate(tab.route) {
                                    popUpTo(Destinations.RECORDS) { saveState = true }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            },
                            icon = { Icon(tab.icon, contentDescription = null) },
                            label = { Text(stringResource(tab.label)) },
                        )
                    }
                }
            }
        },
    ) { padding ->
        NavHost(
            navController = navController,
            startDestination = Destinations.RECORDS,
            modifier = Modifier.padding(padding),
        ) {
            composable(Destinations.RECORDS) {
                val vm: RecordsViewModel = viewModel(factory = factory { RecordsViewModel(recordsRepository) })
                RecordsScreen(vm, onOpen = { navController.navigate(Destinations.editor(it)) })
            }
            composable(Destinations.CONVERSATION) { PendingScreen(stringResource(R.string.tab_conversation)) }
            composable(Destinations.TIMELINE) { PendingScreen(stringResource(R.string.tab_timeline)) }
            composable(Destinations.ACCOUNT) { AccountScreen(email, onSignOut) }
            composable(Destinations.EDITOR) { backStack ->
                val recordId = backStack.arguments?.getString("recordId").orEmpty()
                val vm: EditorViewModel = viewModel(
                    key = "editor-$recordId",
                    factory = factory { EditorViewModel(recordsRepository, recordId) },
                )
                EditorScreen(
                    viewModel = vm,
                    onBack = { navController.popBackStack() },
                    onVersions = { navController.navigate(Destinations.versions(recordId)) },
                )
            }
            composable(Destinations.VERSIONS) { backStack ->
                val recordId = backStack.arguments?.getString("recordId").orEmpty()
                val vm: EditorViewModel = viewModel(
                    key = "editor-$recordId",
                    factory = factory { EditorViewModel(recordsRepository, recordId) },
                )
                VersionsScreen(vm, onBack = { navController.popBackStack() })
            }
        }
    }
}

private fun <T : ViewModel> factory(create: () -> T): ViewModelProvider.Factory =
    object : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <V : ViewModel> create(modelClass: Class<V>): V = create() as V
    }
