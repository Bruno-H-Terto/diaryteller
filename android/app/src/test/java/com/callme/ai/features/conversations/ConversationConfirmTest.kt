package com.callme.ai.features.conversations

import com.callme.ai.core.model.DatePrecision
import com.callme.ai.features.conversations.application.ConversationRepository
import com.callme.ai.features.conversations.application.DiaryMutator
import com.callme.ai.features.conversations.domain.AppliedChange
import com.callme.ai.features.conversations.domain.AppliedKind
import com.callme.ai.features.conversations.domain.ChatEvent
import com.callme.ai.features.conversations.domain.DiaryAction
import com.callme.ai.features.conversations.domain.DiarySnapshot
import com.callme.ai.features.conversations.presentation.ConversationViewModel
import com.callme.ai.features.records.application.RecordsRepository
import com.callme.ai.features.records.domain.Record
import com.callme.ai.features.records.domain.RecordVersion
import com.google.common.truth.Truth.assertThat
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.setMain
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import org.junit.After
import org.junit.Before
import org.junit.Test

/** The gate between an AI suggestion and local diary state. */
@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
class ConversationConfirmTest {

    private class FakeConversation(private val actions: List<DiaryAction>) : ConversationRepository {
        override fun ask(message: String, recordIds: List<String>, recordId: String?): Flow<ChatEvent> =
            flowOf(
                ChatEvent.Started,
                ChatEvent.Delta("Anotei."),
                ChatEvent.Proposed(actions),
                ChatEvent.Completed,
            )
    }

    private class FakeMutator : DiaryMutator {
        var applied: List<DiaryAction> = emptyList()
        var record: String? = null

        override suspend fun snapshot() = DiarySnapshot(emptyList(), emptyList(), "2026-10-20")

        override suspend fun apply(actions: List<DiaryAction>, recordId: String?): List<AppliedChange> {
            applied = actions
            record = recordId
            return listOf(AppliedChange(AppliedKind.EVENT, "Consulta"))
        }
    }

    private class FakeRecords : RecordsRepository {
        var created: String? = null

        override fun observeRecords(): Flow<List<Record>> = flowOf(emptyList())
        override fun observeRecord(recordId: String): Flow<Record?> = flowOf(null)
        override fun observeVersions(recordId: String): Flow<List<RecordVersion>> = flowOf(emptyList())

        override suspend fun createDraft(): String = "draft"

        override suspend fun createRecord(content: String): String {
            created = content
            return "record-1"
        }

        override suspend fun currentContent(recordId: String): String? = null
        override suspend fun updateDraft(recordId: String, content: String) = Unit
        override suspend fun confirmDraft(recordId: String, content: String) = Unit
        override suspend fun addVersion(recordId: String, content: String): String = "v"
        override suspend fun restoreVersion(recordId: String, versionId: String): String = "v"
        override suspend fun setEventDate(recordId: String, isoDate: String?, precision: DatePrecision) = Unit
        override suspend fun deleteRecord(recordId: String) = Unit
        override suspend fun clearAccountData() = Unit
    }

    private val event = DiaryAction.CreateEvent(
        ref = "new:1",
        title = "Consulta da Nina",
        summary = "",
        date = "2026-10-19",
        precision = DatePrecision.DAY,
        participants = emptyList(),
        sourceIds = emptyList(),
        certainty = com.callme.ai.features.conversations.domain.Certainty.EXPLICIT,
    )

    @Before
    fun setUp() = Dispatchers.setMain(UnconfinedTestDispatcher())

    @After
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun `a proposal stays inert until it is confirmed`() = runTest {
        val mutator = FakeMutator()
        val records = FakeRecords()
        val model = ConversationViewModel(FakeConversation(listOf(event)), records, mutator)

        model.ask("Levei a Nina ao veterinário ontem", emptySet())

        val answer = model.state.value.messages.last()
        assertThat(answer.proposals).hasSize(1)
        assertThat(mutator.applied).isEmpty()
        assertThat(records.created).isNull()

        model.confirm(answer.id)

        assertThat(mutator.applied).hasSize(1)
        assertThat(records.created).isEqualTo("Levei a Nina ao veterinário ontem")
        assertThat(mutator.record).isEqualTo("record-1")
        assertThat(model.state.value.messages.last().changes)
            .containsExactly(AppliedChange(AppliedKind.EVENT, "Consulta"))
    }

    @Test
    fun `discarding writes nothing at all`() = runTest {
        val mutator = FakeMutator()
        val records = FakeRecords()
        val model = ConversationViewModel(FakeConversation(listOf(event)), records, mutator)

        model.ask("Levei a Nina ao veterinário ontem", emptySet())
        model.discard(model.state.value.messages.last().id)

        assertThat(mutator.applied).isEmpty()
        assertThat(records.created).isNull()
        assertThat(model.state.value.messages.last().proposals).isEmpty()
    }
}
