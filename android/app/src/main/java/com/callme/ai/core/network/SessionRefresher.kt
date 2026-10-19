package com.callme.ai.core.network

import com.callme.ai.core.security.Session
import com.callme.ai.core.security.SessionStore
import java.time.Instant
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

/**
 * Single-flight refresh. Concurrent callers share one refresh and the new
 * source/token pair is persisted before any caller uses it.
 */
class SessionRefresher(
    private val store: SessionStore,
    private val api: AuthApi,
    private val deviceId: String,
    private val now: () -> Long = { Instant.now().epochSecond },
) {
    private val mutex = Mutex()

    suspend fun refresh(staleAccessToken: String?): Session? = mutex.withLock {
        val current = store.load() ?: return null
        if (staleAccessToken != null && current.accessToken != staleAccessToken) return current
        val response = runCatching { api.refresh(current.source, RefreshRequest(current.refreshToken, deviceId)) }
            .getOrElse {
                store.clear()
                return null
            }
        val renewed = Session(
            accessToken = response.accessToken,
            refreshToken = response.refreshToken,
            source = response.source,
            sessionId = response.sessionId,
            expiresAtEpochSeconds = now() + response.expiresIn,
            sourceExpiresAtEpochSeconds = now() + response.sourceExpiresIn,
            email = current.email,
        )
        store.save(renewed)
        renewed
    }
}
