package com.callme.ai.core.security

import com.google.common.truth.Truth.assertThat
import java.security.MessageDigest
import java.security.SecureRandom
import java.util.Base64
import org.junit.Test

class PkceTest {

    @Test
    fun `verifier has the RFC length and url-safe alphabet`() {
        val pkce = generatePkce(SecureRandom())
        assertThat(pkce.verifier).hasLength(43)
        assertThat(pkce.verifier).matches("^[A-Za-z0-9_-]+$")
    }

    @Test
    fun `challenge is the s256 of the verifier`() {
        val pkce = generatePkce(SecureRandom())
        val expected = Base64.getUrlEncoder().withoutPadding().encodeToString(
            MessageDigest.getInstance("SHA-256").digest(pkce.verifier.toByteArray()),
        )
        assertThat(pkce.challenge).isEqualTo(expected)
        assertThat(pkce.challenge).hasLength(43)
    }

    @Test
    fun `two logins never reuse a verifier`() {
        assertThat(generatePkce().verifier).isNotEqualTo(generatePkce().verifier)
    }
}
