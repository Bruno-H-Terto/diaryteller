package com.callme.ai.core.network

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class OidcStartRequest(
    val provider: String,
    @SerialName("redirect_uri") val redirectUri: String,
    @SerialName("device_id") val deviceId: String,
    @SerialName("code_challenge") val codeChallenge: String,
    @SerialName("code_challenge_method") val codeChallengeMethod: String = "S256",
)

@Serializable
data class OidcTransactionDto(
    @SerialName("transaction_id") val transactionId: String,
    @SerialName("authorization_url") val authorizationUrl: String,
    val state: String,
    @SerialName("expires_at") val expiresAt: String,
)

@Serializable
data class OidcExchangeRequest(
    @SerialName("transaction_id") val transactionId: String,
    val code: String,
    val state: String,
    @SerialName("code_verifier") val codeVerifier: String,
)

@Serializable
data class RefreshRequest(
    @SerialName("refresh_token") val refreshToken: String,
    @SerialName("device_id") val deviceId: String,
)

@Serializable
data class TokenResponseDto(
    @SerialName("access_token") val accessToken: String,
    @SerialName("refresh_token") val refreshToken: String,
    val source: String,
    @SerialName("session_id") val sessionId: String,
    @SerialName("expires_in") val expiresIn: Long,
    @SerialName("source_expires_in") val sourceExpiresIn: Long,
)

@Serializable
data class MeDto(val id: String, val email: String)
