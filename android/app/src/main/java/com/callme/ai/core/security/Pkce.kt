package com.callme.ai.core.security

import java.security.MessageDigest
import java.security.SecureRandom
import java.util.Base64

/** PKCE verifier and S256 challenge for the authorization-code flow. */
data class Pkce(val verifier: String, val challenge: String)

fun generatePkce(random: SecureRandom = SecureRandom()): Pkce {
    val bytes = ByteArray(32).also(random::nextBytes)
    val verifier = bytes.base64Url()
    val digest = MessageDigest.getInstance("SHA-256").digest(verifier.toByteArray(Charsets.US_ASCII))
    return Pkce(verifier = verifier, challenge = digest.base64Url())
}

private fun ByteArray.base64Url(): String =
    Base64.getUrlEncoder().withoutPadding().encodeToString(this)
