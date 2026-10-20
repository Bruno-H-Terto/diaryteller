package com.callme.ai.navigation

import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavGraphBuilder
import androidx.navigation.NavHostController
import androidx.navigation.compose.composable
import com.callme.ai.features.connections.application.ConnectionsRepository
import com.callme.ai.features.connections.presentation.ConnectionsScreen
import com.callme.ai.features.connections.presentation.ConnectionsViewModel
import com.callme.ai.features.connections.presentation.EventDetailScreen
import com.callme.ai.features.connections.presentation.EventViewModel
import com.callme.ai.features.entities.application.EntitiesRepository
import com.callme.ai.features.entities.presentation.EntitiesViewModel
import com.callme.ai.features.entities.presentation.EntityDetailScreen
import com.callme.ai.features.entities.presentation.EntityDetailViewModel
import com.callme.ai.features.entities.presentation.EntityCreateScreen
import com.callme.ai.features.entities.presentation.EntityListScreen

/** Connections, entity registry and event detail routes. */
fun NavGraphBuilder.detailRoutes(
    navController: NavHostController,
    connectionsRepository: ConnectionsRepository,
    entitiesRepository: EntitiesRepository,
) {
            composable(Destinations.CONNECTIONS) {
                val vm: ConnectionsViewModel = viewModel(
                    factory = factory { ConnectionsViewModel(connectionsRepository, entitiesRepository) },
                )
                ConnectionsScreen(
                    viewModel = vm,
                    onOpenEntity = { id, month -> navController.navigate(Destinations.entity(id, month)) },
                    onEditEntity = { navController.navigate(Destinations.avatar(it)) },
                    onOpenEvent = { navController.navigate(Destinations.event(it)) },
                    onOpenRecord = { navController.navigate(Destinations.editor(it)) },
                    onManageEntities = { navController.navigate(Destinations.ENTITIES) },
                )
            }
            composable(Destinations.ENTITIES) {
                val vm: EntitiesViewModel = viewModel(
                    factory = factory { EntitiesViewModel(entitiesRepository) },
                )
                EntityListScreen(
                    viewModel = vm,
                    onBack = { navController.popBackStack() },
                    onOpen = { navController.navigate(Destinations.entity(it)) },
                    onAdd = { navController.navigate(Destinations.ENTITY_NEW) },
                )
            }
            composable(Destinations.ENTITY_NEW) {
                val vm: EntitiesViewModel = viewModel(
                    factory = factory { EntitiesViewModel(entitiesRepository) },
                )
                EntityCreateScreen(
                    viewModel = vm,
                    onBack = { navController.popBackStack() },
                    onCreated = { id ->
                        navController.popBackStack()
                        navController.navigate(Destinations.avatar(id))
                    },
                )
            }
            composable(
                route = Destinations.ENTITY,
                arguments = listOf(
                    androidx.navigation.navArgument("mes") { defaultValue = "" },
                ),
            ) { backStack ->
                val entityId = backStack.arguments?.getString("entityId").orEmpty()
                val month = backStack.arguments?.getString("mes").orEmpty()
                val vm: EntityDetailViewModel = viewModel(
                    key = "entity-$entityId",
                    factory = factory { EntityDetailViewModel(entitiesRepository, entityId, month) },
                )
                EntityDetailScreen(
                    viewModel = vm,
                    onBack = { navController.popBackStack() },
                    onEdit = { navController.navigate(Destinations.avatar(entityId)) },
                    onOpenEvent = { navController.navigate(Destinations.event(it)) },
                    onOpenRecord = { navController.navigate(Destinations.editor(it)) },
                )
            }
            composable(Destinations.AVATAR) { backStack ->
                val entityId = backStack.arguments?.getString("entityId").orEmpty()
                EntityEditorRoute(
                    entityId = entityId,
                    entitiesRepository = entitiesRepository,
                    navController = navController,
                )
            }
            composable(Destinations.EVENT) { backStack ->
                val eventId = backStack.arguments?.getString("eventId").orEmpty()
                val vm: EventViewModel = viewModel(
                    key = "event-$eventId",
                    factory = factory { EventViewModel(connectionsRepository, eventId) },
                )
                EventDetailScreen(
                    viewModel = vm,
                    onBack = { navController.popBackStack() },
                    onOpenRecord = { navController.navigate(Destinations.editor(it)) },
                )
            }
}
