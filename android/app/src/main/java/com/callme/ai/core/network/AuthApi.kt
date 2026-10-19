package com.callme.ai.core.network

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST

interface AuthApi {
    @POST("v1/auth/oidc/transactions")
    suspend fun startOidc(@Body body: OidcStartRequest): OidcTransactionDto

    @POST("v1/auth/oidc/exchange")
    suspend fun exchangeOidc(@Body body: OidcExchangeRequest): TokenResponseDto

    @POST("v1/auth/refresh")
    suspend fun refresh(
        @Header("X-Session-Source") source: String,
        @Body body: RefreshRequest,
    ): TokenResponseDto

    @GET("v1/me")
    suspend fun me(): MeDto
}
