package com.callme.ai.core.security

import android.content.Context
import java.io.File
import java.security.SecureRandom
import java.util.Base64

/** Stores one encrypted secret (for example the SQLCipher passphrase) in app-private files. */
class SecretFile(private val context: Context, private val name: String, private val cipher: CipherBox) {

    fun getOrCreate(): ByteArray {
        val file = File(context.filesDir, name)
        if (file.exists()) {
            return cipher.decrypt(Base64.getDecoder().decode(file.readText()))
        }
        val secret = ByteArray(32).also(SecureRandom()::nextBytes)
        file.writeText(Base64.getEncoder().encodeToString(cipher.encrypt(secret)))
        return secret
    }
}
