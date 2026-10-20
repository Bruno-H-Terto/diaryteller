package com.callme.ai.features.connections

import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import com.callme.ai.core.database.CallMeDatabase
import com.callme.ai.core.database.DiaryEntity
import com.callme.ai.core.database.RecordEntity
import com.callme.ai.core.database.RecordEntityLink
import com.callme.ai.core.database.RecordMetadataEntity
import com.callme.ai.core.database.RecordVersionEntity
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
class ConnectionsCountingTest {

    private lateinit var database: CallMeDatabase
    private val dao get() = database.connectionsDao()
    private val entities get() = database.entitiesDao()

    @Before
    fun setUp() {
        database = Room.inMemoryDatabaseBuilder(
            ApplicationProvider.getApplicationContext(),
            CallMeDatabase::class.java,
        ).allowMainThreadQueries().build()
    }

    @After
    fun tearDown() = database.close()

    @Test
    fun `repeated mentions of the same entity count once per record`() = runTest {
        addPerson("ana", "Ana")
        addRecord("r1", "2026-10-19")
        addRecord("r2", "2026-10-19")
        repeat(3) { entities.upsertLink(link("r1", "ana")) }
        entities.upsertLink(link("r2", "ana"))

        assertThat(countOf("ana")).isEqualTo(2)
    }

    @Test
    fun `versions of one record never inflate the frequency`() = runTest {
        addPerson("marina", "Marina")
        addRecord("r1", "2026-10-19")
        listOf(1, 2, 3).forEach { number ->
            database.recordsDao().insertVersion(
                RecordVersionEntity(
                    id = "r1-v$number",
                    recordId = "r1",
                    number = number,
                    content = "v$number",
                    origin = "USER",
                    baseVersionId = null,
                    createdAt = 1L,
                    confirmed = true,
                ),
            )
        }
        entities.upsertLink(link("r1", "marina"))

        assertThat(countOf("marina")).isEqualTo(1)
    }

    @Test
    fun `suggested links stay out of the confirmed count`() = runTest {
        addPerson("nina", "Nina")
        addRecord("r1", "2026-10-19")
        addRecord("r2", "2026-10-19")
        entities.upsertLink(link("r1", "nina"))
        entities.upsertLink(link("r2", "nina", review = "SUGGESTED"))

        assertThat(countOf("nina")).isEqualTo(1)
        assertThat(dao.reviewItems().first()).hasSize(1)
    }

    @Test
    fun `period filter excludes records from other months`() = runTest {
        addPerson("ana", "Ana")
        addRecord("oct", "2026-10-19")
        addRecord("sep", "2026-09-19")
        entities.upsertLink(link("oct", "ana"))
        entities.upsertLink(link("sep", "ana"))

        val october = dao.connectionsFlow("2026-10-01", "2026-10-31", null, "", 20).first()
        val september = dao.connectionsFlow("2026-09-01", "2026-09-30", null, "", 20).first()

        assertThat(october.single().recordCount).isEqualTo(1)
        assertThat(september.single().recordCount).isEqualTo(1)
    }

    @Test
    fun `two people with the same name remain distinct entities`() = runTest {
        addPerson("marina-1", "Marina")
        addPerson("marina-2", "Marina")
        addRecord("r1", "2026-10-19")
        addRecord("r2", "2026-10-19")
        entities.upsertLink(link("r1", "marina-1"))
        entities.upsertLink(link("r2", "marina-2"))

        val rows = dao.connectionsFlow("2026-10-01", "2026-10-31", null, "", 20).first()

        assertThat(rows.map { it.id }).containsExactly("marina-1", "marina-2")
    }

    private suspend fun countOf(entityId: String): Int =
        dao.connectionsFlow("2026-10-01", "2026-10-31", null, "", 20).first()
            .first { it.id == entityId }.recordCount

    private suspend fun addPerson(id: String, name: String) = entities.insert(
        DiaryEntity(id, "PERSON", name, "p1", 0xFFEAE5F6, null, null, null, 1L, 1L),
    )

    private suspend fun addRecord(id: String, day: String) {
        database.recordsDao().insertRecord(
            RecordEntity(id, "$id-v1", 1L, 1L, "LOCAL", null, "texto"),
        )
        database.recordsDao().insertMetadata(
            RecordMetadataEntity(id, day, null, null, null, "UNKNOWN", "DONE"),
        )
    }

    private fun link(recordId: String, entityId: String, review: String = "CONFIRMED") =
        RecordEntityLink(recordId, entityId, "DECLARED", review)
}
