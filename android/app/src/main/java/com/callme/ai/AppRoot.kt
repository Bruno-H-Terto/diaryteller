package com.callme.ai

import android.net.Uri
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.callme.ai.bootstrap.AppContainer
import com.callme.ai.features.auth.domain.AuthState
import com.callme.ai.features.auth.presentation.AuthScreen
import com.callme.ai.features.auth.presentation.AuthViewModel
import com.callme.ai.navigation.MainScaffold

@Composable
fun AppRoot(container: AppContainer, redirect: Uri?, onRedirectHandled: () -> Unit) {
    val authVm: AuthViewModel = viewModel(
        factory = object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T =
                AuthViewModel(
                    container.authRepository,
                    onSignOut = { container.recordsRepository.clearAccountData() },
                ) as T
        },
    )
    LaunchedEffect(Unit) { authVm.restore() }
    LaunchedEffect(redirect) {
        redirect?.let {
            authVm.handleRedirect(it)
            onRedirectHandled()
        }
    }
    val state by authVm.state.collectAsStateWithLifecycle()
    when (val current = state) {
        is AuthState.Loading -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            CircularProgressIndicator()
        }
        is AuthState.SignedOut, is AuthState.Failed -> AuthScreen(authVm, container.oidcProvider)
        is AuthState.SignedIn -> MainScaffold(
            recordsRepository = container.recordsRepository,
            captureService = container.captureService,
            email = current.email,
            onSignOut = authVm::signOut,
        )
    }
}
