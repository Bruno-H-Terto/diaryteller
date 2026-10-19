package com.callme.ai

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.callme.ai.core.database.DatabaseFactory
import com.callme.ai.core.security.KeystoreCipherBox
import com.callme.ai.core.security.SecretFile
import com.callme.ai.features.records.adapters.RoomRecordsRepository
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class DatabaseInstrumentedTest {

    @Test
    fun sqlCipherDatabasePersistsAConfirmedVersion() = runBlocking {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val cipher = KeystoreCipherBox("test.database")
        val database = DatabaseFactory(context, SecretFile(context, "instrumented.key", cipher)).open()
        try {
            val repository = RoomRecordsRepository(database.recordsDao())
            val recordId = repository.createDraft()
            repository.confirmDraft(recordId, "conteúdo de teste")
            val versions = repository.observeVersions(recordId).first()
            assertEquals(1, versions.size)
            assertEquals("conteúdo de teste", versions.single().content)
        } finally {
            database.close()
        }
    }
}
