package com.callme.ai.navigation

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import com.callme.ai.features.entities.application.EntitiesRepository
import com.callme.ai.features.entities.presentation.AvatarEditorScreen
import com.callme.ai.features.entities.presentation.AvatarEditorViewModel

/** Loads the current identity before opening the avatar editor. */
@Composable
fun EntityEditorRoute(
    entityId: String,
    entitiesRepository: EntitiesRepository,
    navController: NavHostController,
) {
    val entities by entitiesRepository.observeEntities().collectAsStateWithLifecycle(initialValue = emptyList())
    val entity = entities.firstOrNull { it.id == entityId }
    if (entity == null) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
        return
    }
    val vm: AvatarEditorViewModel = viewModel(
        key = "avatar-$entityId",
        factory = factory {
            AvatarEditorViewModel(entitiesRepository, entityId, entity.avatar, entity.name)
        },
    )
    AvatarEditorScreen(viewModel = vm, type = entity.type, onBack = { navController.popBackStack() })
}
