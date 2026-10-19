package com.callme.ai.features.auth.adapters

import android.net.Uri
import com.callme.ai.core.network.AuthApi
import com.callme.ai.core.network.OidcExchangeRequest
import com.callme.ai.core.network.OidcStartRequest
import com.callme.ai.core.security.Pkce
import com.callme.ai.core.security.Session
import com.callme.ai.core.security.SessionStore
import com.callme.ai.core.security.generatePkce
import com.callme.ai.features.auth.application.AuthRepository
import com.callme.ai.features.auth.application.DeviceIdStore
import com.callme.ai.features.auth.domain.AuthFailure
import com.callme.ai.features.auth.domain.AuthState
import com.callme.ai.features.auth.domain.CallbackResult
import java.time.Instant
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * Authorization Code + PKCE through the system browser. No client secret and no
 * WebView: the backend owns the provider exchange.
 */
class OidcAuthRepository(
    private val api: AuthApi,
    private val sessionStore: SessionStore,
    private val deviceIds: DeviceIdStore,
    private val redirectUri: String,
    private val now: () -> Long = { Instant.now().epochSecond },
) : AuthRepository {

    private data class Pending(val transactionId: String, val state: String, val pkce: Pkce)

    private val _state = MutableStateFlow<AuthState>(AuthState.Loading)
    override val state: StateFlow<AuthState> = _state.asStateFlow()
    private var pending: Pending? = null

    override suspend fun restore() {
        val session = sessionStore.load()
        _state.value = if (session == null) {
            AuthState.SignedOut
        } else {
            AuthState.SignedIn(session.email ?: "conta local", session.sessionId)
        }
    }

    override suspend fun startSignIn(provider: String): Result<String> = runCatching {
        val deviceId = deviceIds.get()
        val pkce = generatePkce()
        val transaction = api.startOidc(
            OidcStartRequest(
                provider = provider,
                redirectUri = redirectUri,
                deviceId = deviceId,
                codeChallenge = pkce.challenge,
            ),
        )
        pending = Pending(transaction.transactionId, transaction.state, pkce)
        transaction.authorizationUrl
    }.onFailure { _state.value = AuthState.Failed(AuthFailure.PROVIDER_UNAVAILABLE) }

    override suspend fun handleRedirect(uri: Uri): CallbackResult {
        val current = pending ?: return CallbackResult.Invalid(AuthFailure.INVALID_CALLBACK)
        if (uri.getQueryParameter("error") != null) {
            pending = null
            return CallbackResult.Cancelled
        }
        val code = uri.getQueryParameter("code")
        val state = uri.getQueryParameter("state")
        if (code.isNullOrBlank() || state.isNullOrBlank() || state != current.state) {
            return CallbackResult.Invalid(AuthFailure.INVALID_CALLBACK)
        }
        return runCatching {
            val tokens = api.exchangeOidc(
                OidcExchangeRequest(current.transactionId, code, state, current.pkce.verifier),
            )
            val session = Session(
                accessToken = tokens.accessToken,
                refreshToken = tokens.refreshToken,
                source = tokens.source,
                sessionId = tokens.sessionId,
                expiresAtEpochSeconds = now() + tokens.expiresIn,
                sourceExpiresAtEpochSeconds = now() + tokens.sourceExpiresIn,
            )
            sessionStore.save(session)
            val me = runCatching { api.me() }.getOrNull()
            val withEmail = session.copy(email = me?.email)
            sessionStore.save(withEmail)
            pending = null
            _state.value = AuthState.SignedIn(withEmail.email ?: "conta", withEmail.sessionId)
            CallbackResult.Success
        }.getOrElse {
            _state.value = AuthState.Failed(AuthFailure.NETWORK)
            CallbackResult.Invalid(AuthFailure.NETWORK)
        }
    }

    override suspend fun signOut() {
        pending = null
        sessionStore.clear()
        _state.value = AuthState.SignedOut
    }
}
