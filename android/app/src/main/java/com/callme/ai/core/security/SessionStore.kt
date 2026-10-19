package com.callme.ai.core.security

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import java.util.Base64
import kotlinx.coroutines.flow.first
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

@Serializable
data class Session(
    val accessToken: String,
    val refreshToken: String,
    val source: String,
    val sessionId: String,
    val expiresAtEpochSeconds: Long,
    val sourceExpiresAtEpochSeconds: Long,
    val email: String? = null,
)

/** Stores the only durable credential material, encrypted before it touches disk. */
interface SessionStore {
    suspend fun load(): Session?
    suspend fun save(session: Session)
    suspend fun clear()
}

private val Context.sessionData by preferencesDataStore(name = "callme_session")

class EncryptedSessionStore(
    private val context: Context,
    private val cipher: CipherBox,
) : SessionStore {
    private val key = stringPreferencesKey("session")
    private val json = Json { ignoreUnknownKeys = true }

    override suspend fun load(): Session? {
        val stored = context.sessionData.data.first()[key] ?: return null
        return runCatching {
            val plain = cipher.decrypt(Base64.getDecoder().decode(stored))
            json.decodeFromString(Session.serializer(), plain.toString(Charsets.UTF_8))
        }.getOrNull()
    }

    override suspend fun save(session: Session) {
        val plain = json.encodeToString(Session.serializer(), session).toByteArray()
        val encrypted = Base64.getEncoder().encodeToString(cipher.encrypt(plain))
        context.sessionData.edit { it[key] = encrypted }
    }

    override suspend fun clear() {
        context.sessionData.edit { it.remove(key) }
    }
}
