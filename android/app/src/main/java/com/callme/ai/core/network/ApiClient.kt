package com.callme.ai.core.network

import com.callme.ai.BuildConfig
import com.callme.ai.core.security.SessionStore
import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.json.Json
import okhttp3.Interceptor
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import retrofit2.Retrofit

/** One place that knows how to reach the backend and attach session credentials. */
class ApiClient(
    private val sessionStore: SessionStore,
    private val baseUrl: String = BuildConfig.BACKEND_BASE_URL,
) {
    private val json = Json { ignoreUnknownKeys = true; explicitNulls = false }

    private val sessionInterceptor = Interceptor { chain ->
        val request = chain.request()
        val session = runBlocking { sessionStore.load() }
        val builder = request.newBuilder()
        if (session != null && !request.url.encodedPath.startsWith("/v1/auth/")) {
            builder
                .header("Authorization", "Bearer ${session.accessToken}")
                .header("X-Session-Source", session.source)
        }
        chain.proceed(builder.build())
    }

    val http: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .addInterceptor(sessionInterceptor)
        .build()

    val retrofit: Retrofit = Retrofit.Builder()
        .baseUrl(baseUrl)
        .client(http)
        .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
        .build()

    val authApi: AuthApi = retrofit.create(AuthApi::class.java)

    /** Refresh uses a separate client so a 401 can never recurse through the interceptor. */
    fun refreshClient(): AuthApi = Retrofit.Builder()
        .baseUrl(baseUrl)
        .client(OkHttpClient.Builder().connectTimeout(15, TimeUnit.SECONDS).build())
        .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
        .build()
        .create(AuthApi::class.java)
}
