package com.callme.ai.features.auth.domain

/** Stable view of the local session for the UI. */
sealed interface AuthState {
    data object Loading : AuthState
    data object SignedOut : AuthState
    data class SignedIn(val email: String, val sessionId: String) : AuthState
    data class Failed(val reason: AuthFailure) : AuthState
}

enum class AuthFailure {
    PROVIDER_UNAVAILABLE,
    INVALID_CALLBACK,
    CANCELLED,
    NETWORK,
}

data class SignInUrl(val url: String)

/** Why a callback could not be accepted; the UI maps this to a useful message. */
sealed interface CallbackResult {
    data object Success : CallbackResult
    data object Cancelled : CallbackResult
    data class Invalid(val reason: AuthFailure) : CallbackResult
}
