package com.callme.ai.core.network

import com.callme.ai.BuildConfig
import com.callme.ai.core.security.SessionStore
import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.json.Json
import okhttp3.Authenticator
import okhttp3.Interceptor
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import retrofit2.Retrofit

/** One place that knows how to reach the backend and attach session credentials. */
class ApiClient(
    private val sessionStore: SessionStore,
    private val baseUrl: String = BuildConfig.BACKEND_BASE_URL,
    private val conversationBaseUrl: String = BuildConfig.CONVERSATION_BASE_URL,
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

    /** Set by the container once the refresher exists; used on 401 only. */
    var refresher: SessionRefresher? = null

    private val reauth = Authenticator { _, response ->
        val stale = response.request.header("Authorization")?.removePrefix("Bearer ")
        val renewed = refresher?.let { runBlocking { it.refresh(stale) } }
        if (response.priorResponse != null || renewed == null) {
            null
        } else {
            response.request.newBuilder()
                .header("Authorization", "Bearer ${renewed.accessToken}")
                .header("X-Session-Source", renewed.source)
                .build()
        }
    }

    val http: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .addInterceptor(sessionInterceptor)
        .authenticator(reauth)
        .build()

    val retrofit: Retrofit = Retrofit.Builder()
        .baseUrl(baseUrl)
        .client(http)
        .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
        .build()

    val authApi: AuthApi = retrofit.create(AuthApi::class.java)

    val conversationApi: ConversationApi = Retrofit.Builder()
        .baseUrl(conversationBaseUrl)
        .client(http)
        .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
        .build()
        .create(ConversationApi::class.java)

    /** Refresh uses a separate client so a 401 can never recurse through the interceptor. */
    fun refreshClient(): AuthApi = Retrofit.Builder()
        .baseUrl(baseUrl)
        .client(OkHttpClient.Builder().connectTimeout(15, TimeUnit.SECONDS).build())
        .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
        .build()
        .create(AuthApi::class.java)
}
