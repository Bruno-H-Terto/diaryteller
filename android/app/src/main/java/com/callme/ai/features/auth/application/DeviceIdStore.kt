package com.callme.ai.features.auth.application

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import java.util.UUID
import kotlinx.coroutines.flow.first

private val Context.deviceData by preferencesDataStore(name = "callme_device")

/** Random installation id. It is not a secret and is stable across logins. */
class DeviceIdStore(private val context: Context) {
    private val key = stringPreferencesKey("device_id")

    suspend fun get(): String {
        context.deviceData.data.first()[key]?.let { return it }
        val created = UUID.randomUUID().toString()
        context.deviceData.edit { it[key] = created }
        return created
    }
}
