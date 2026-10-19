package com.callme.ai.core.security

import android.content.Context
import androidx.security.crypto.EncryptedFile
import androidx.security.crypto.MasterKey
import java.io.File
import java.io.InputStream
import java.io.OutputStream

/**
 * Streams app-private files through AES-256-GCM with a Keystore-backed master
 * key. Large audio never has to fit in memory, and no custom crypto is used.
 */
class EncryptedFiles(context: Context) {

    private val appContext = context.applicationContext
    private val masterKey: MasterKey = MasterKey.Builder(appContext)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()

    fun write(target: File): OutputStream = encrypted(target).openFileOutput()

    fun read(source: File): InputStream = encrypted(source).openFileInput()

    fun copyInto(source: File, target: File) {
        target.parentFile?.mkdirs()
        source.inputStream().use { input ->
            write(target).use { output -> input.copyTo(output, DEFAULT_BUFFER) }
        }
    }

    fun copyOut(source: File, target: File) {
        target.parentFile?.mkdirs()
        read(source).use { input ->
            target.outputStream().use { output -> input.copyTo(output, DEFAULT_BUFFER) }
        }
    }

    private fun encrypted(file: File): EncryptedFile = EncryptedFile.Builder(
        appContext,
        file,
        masterKey,
        EncryptedFile.FileEncryptionScheme.AES256_GCM_HKDF_4KB,
    ).build()

    private companion object {
        const val DEFAULT_BUFFER = 64 * 1024
    }
}
