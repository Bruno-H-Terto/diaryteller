package com.callme.ai.features.records

import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import com.callme.ai.core.database.CallMeDatabase
import com.callme.ai.features.records.adapters.RoomRecordsRepository
import com.callme.ai.features.records.domain.VersionOrigin
import com.google.common.truth.Truth.assertThat
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.runTest
import org.junit.After
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35], application = com.callme.ai.TestApplication::class)
class RoomRecordsRepositoryTest {

    private lateinit var database: CallMeDatabase
    private lateinit var repository: RoomRecordsRepository

    @Before
    fun setUp() {
        database = Room.inMemoryDatabaseBuilder(
            ApplicationProvider.getApplicationContext(),
            CallMeDatabase::class.java,
        ).allowMainThreadQueries().build()
        repository = RoomRecordsRepository(database.recordsDao())
    }

    @After
    fun tearDown() = database.close()

    @Test
    fun `confirm then edit keeps the original and appends a version`() = runTest {
        val recordId = repository.createDraft()
        repository.confirmDraft(recordId, "original")
        val v2 = repository.addVersion(recordId, "editado")

        val versions = repository.observeVersions(recordId).first()
        assertThat(versions.map { it.number }).containsExactly(1, 2).inOrder()
        assertThat(versions.first().content).isEqualTo("original")
        assertThat(versions.first().confirmed).isTrue()
        assertThat(versions.last().id).isEqualTo(v2)
        assertThat(versions.last().baseVersionId).isEqualTo(versions.first().id)
    }

    @Test
    fun `restoring an old version creates a new version instead of rewriting`() = runTest {
        val recordId = repository.createDraft()
        repository.confirmDraft(recordId, "original")
        repository.addVersion(recordId, "segunda")
        val original = repository.observeVersions(recordId).first().first()

        repository.restoreVersion(recordId, original.id)

        val versions = repository.observeVersions(recordId).first()
        assertThat(versions).hasSize(3)
        assertThat(versions.map { it.number }).containsExactly(1, 2, 3).inOrder()
        assertThat(versions.last().origin).isEqualTo(VersionOrigin.RESTORE)
        assertThat(versions.last().content).isEqualTo("original")
        assertThat(versions.first().content).isEqualTo("original")
    }

    @Test
    fun `draft updates never touch a confirmed version`() = runTest {
        val recordId = repository.createDraft()
        repository.confirmDraft(recordId, "confirmado")
        repository.updateDraft(recordId, "tentativa")

        assertThat(repository.observeVersions(recordId).first().last().content).isEqualTo("confirmado")
    }

    @Test
    fun `logout clears every account-scoped row`() = runTest {
        val recordId = repository.createDraft()
        repository.confirmDraft(recordId, "conteúdo")
        repository.clearAccountData()

        assertThat(repository.observeRecords().first()).isEmpty()
    }
}
