package com.callme.ai.features.auth.application

import android.net.Uri
import com.callme.ai.features.auth.domain.AuthState
import com.callme.ai.features.auth.domain.CallbackResult
import kotlinx.coroutines.flow.StateFlow

/** Boundary the UI uses; the OIDC adapter implements it. */
interface AuthRepository {
    val state: StateFlow<AuthState>

    suspend fun restore()

    suspend fun startSignIn(provider: String): Result<String>

    suspend fun handleRedirect(uri: Uri): CallbackResult

    suspend fun signOut()
}
