package com.callme.ai.core.security

import androidx.test.core.app.ApplicationProvider
import com.google.common.truth.Truth.assertThat
import kotlinx.coroutines.test.runTest
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35], application = com.callme.ai.TestApplication::class)
class SessionStoreTest {

    private class ReversingCipher : CipherBox {
        override fun encrypt(plain: ByteArray): ByteArray = plain.reversedArray()
        override fun decrypt(payload: ByteArray): ByteArray = payload.reversedArray()
    }

    private lateinit var store: EncryptedSessionStore

    @Before
    fun setUp() = runTest {
        store = EncryptedSessionStore(ApplicationProvider.getApplicationContext(), ReversingCipher())
        store.clear()
    }

    @Test
    fun `round trip keeps every credential field`() = runTest {
        val session = Session("a", "r", "s", "session", 10, 20, "user@example.com")
        store.save(session)
        assertThat(store.load()).isEqualTo(session)
    }

    @Test
    fun `clear removes the session`() = runTest {
        store.save(Session("a", "r", "s", "session", 10, 20))
        store.clear()
        assertThat(store.load()).isNull()
    }

    @Test
    fun `unreadable ciphertext is treated as signed out`() = runTest {
        store.save(Session("a", "r", "s", "session", 10, 20))
        val broken = EncryptedSessionStore(
            ApplicationProvider.getApplicationContext(),
            object : CipherBox {
                override fun encrypt(plain: ByteArray) = plain
                override fun decrypt(payload: ByteArray): ByteArray = error("wrong key")
            },
        )
        assertThat(broken.load()).isNull()
    }
}
