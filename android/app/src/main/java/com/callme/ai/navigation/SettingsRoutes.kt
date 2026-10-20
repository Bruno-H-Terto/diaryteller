package com.callme.ai.navigation

import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavGraphBuilder
import androidx.navigation.NavHostController
import androidx.navigation.compose.composable
import com.callme.ai.core.database.SampleDiary
import com.callme.ai.features.settings.presentation.AccountScreen
import com.callme.ai.features.settings.presentation.PrivacyScreen
import com.callme.ai.features.settings.presentation.SampleDataViewModel
import com.callme.ai.features.settings.presentation.SettingsScreen

/** Settings hub, privacy and account routes. */
fun NavGraphBuilder.settingsRoutes(
    navController: NavHostController,
    sampleDiary: SampleDiary,
    email: String,
    onSignOut: () -> Unit,
) {
            composable(Destinations.SETTINGS) {
                val sample: SampleDataViewModel = viewModel(
                    factory = factory { SampleDataViewModel(sampleDiary) },
                )
                SettingsScreen(
                    onPrivacy = { navController.navigate(Destinations.PRIVACY) },
                    onAccount = { navController.navigate(Destinations.ACCOUNT) },
                    sample = sample,
                )
            }
            composable(Destinations.PRIVACY) {
                SubScreen(onBack = { navController.popBackStack() }) { PrivacyScreen() }
            }
            composable(Destinations.ACCOUNT) {
                AccountScreen(
                    email = email,
                    onBack = { navController.popBackStack() },
                    onSignOut = onSignOut,
                )
            }
}
