package com.callme.ai.features.auth.presentation

import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.callme.ai.features.auth.application.AuthRepository
import com.callme.ai.features.auth.domain.AuthState
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class AuthViewModel(
    private val repository: AuthRepository,
    private val onSignOut: suspend () -> Unit = {},
) : ViewModel() {

    val state: StateFlow<AuthState> = repository.state
    private val _launchUrl = MutableStateFlow<String?>(null)
    val launchUrl: StateFlow<String?> = _launchUrl.asStateFlow()

    fun restore() = viewModelScope.launch { repository.restore() }

    fun startSignIn(provider: String) = viewModelScope.launch {
        repository.startSignIn(provider).onSuccess { _launchUrl.value = it }
    }

    fun consumeLaunchUrl() {
        _launchUrl.value = null
    }

    fun handleRedirect(uri: Uri) = viewModelScope.launch { repository.handleRedirect(uri) }

    fun signOut() = viewModelScope.launch {
        onSignOut()
        repository.signOut()
    }
}
