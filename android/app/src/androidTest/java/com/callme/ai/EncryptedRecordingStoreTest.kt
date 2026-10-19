package com.callme.ai

import androidx.room.Room
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.callme.ai.core.database.CallMeDatabase
import com.callme.ai.core.security.EncryptedFiles
import com.callme.ai.features.capture.adapters.EncryptedRecordingStore
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class EncryptedRecordingStoreTest {

    private val context = InstrumentationRegistry.getInstrumentation().targetContext
    private lateinit var database: CallMeDatabase
    private lateinit var store: EncryptedRecordingStore

    @Before
    fun setUp() {
        database = Room.inMemoryDatabaseBuilder(context, CallMeDatabase::class.java).build()
        store = EncryptedRecordingStore(context, database.recordsDao(), EncryptedFiles(context))
    }

    @After
    fun tearDown() = database.close()

    @Test
    fun voiceNoteIsEncryptedAtRestAndPlayable() {
        val marker = "conteudo-de-audio-em-claro".toByteArray()
        val temporary = java.io.File.createTempFile("voice-", ".m4a", context.cacheDir)
        temporary.writeBytes(marker)

        val saved = store.save(temporary, 2_000)
        val stored = java.io.File(context.filesDir, "recordings/${saved.id}.enc")
        assertTrue(stored.exists())
        assertFalse(String(stored.readBytes(), Charsets.ISO_8859_1).contains("conteudo-de-audio"))
        assertFalse(temporary.exists())

        val playback = store.materialize(saved.id)
        assertNotNull(playback)
        assertTrue(playback!!.readBytes().contentEquals(marker))
        playback.delete()
    }

    @Test
    fun deletingRemovesTheEncryptedFile() {
        val temporary = java.io.File.createTempFile("voice-", ".m4a", context.cacheDir)
        temporary.writeText("audio")
        val saved = store.save(temporary, 1_000)
        val stored = java.io.File(context.filesDir, "recordings/${saved.id}.enc")
        assertTrue(stored.exists())

        store.delete(saved.id)

        assertFalse(stored.exists())
        assertEquals(0, runBlocking { database.recordsDao().recordings().size })
    }
}
