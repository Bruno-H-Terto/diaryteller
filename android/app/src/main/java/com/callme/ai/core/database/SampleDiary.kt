package com.callme.ai.core.database

import com.callme.ai.core.media.MediaStore
import java.time.LocalDate
import java.time.LocalTime
import java.time.ZoneId
import kotlinx.coroutines.flow.Flow

/**
 * Installable synthetic diary used to validate grouping, frequency, versions,
 * namesakes and date precision. Every row is prefixed with `sample-`, so it can
 * be removed without touching real entries and never resets the database.
 */
class SampleDiary(
    private val records: RecordsDao,
    private val entities: EntitiesDao,
    private val media: MediaStore,
) {

    fun observeInstalled(): Flow<Int> = records.observeSampleCount()

    /** Adds the dataset; existing rows are kept untouched. */
    suspend fun insert() {
        entities.insertSampleEntities()
        val audio = media.saveRecording(SampleAudio.tone(), 1_200)
        val ids = insertRecords(audio.id)
        entities.insertSampleEvents(ids)
    }

    /** Removes only the synthetic rows and their encrypted audio. */
    suspend fun remove() {
        records.sampleRecordingIds().forEach { media.deleteRecording(it) }
        records.deleteSampleRecords()
        entities.deleteSampleEvents()
        entities.deleteSampleEntities()
    }

    private suspend fun insertRecords(audioId: String): List<String> {
        val ids = mutableListOf(
            record("sample-r1", "2026-10-19", "09:12", "Quero reservar um tempo para o meu projeto."),
            record(
                "sample-r2",
                "2026-10-19",
                "11:35",
                "Almocei com a Ana do trabalho. Falamos da mudança para Curitiba em 2019.",
                audioId,
            ),
            record("sample-r3", "2026-10-19", "20:10", "Minha irmã Marina me ajudou naquela mudança."),
            record("sample-r4", "2026-10-18", "08:00", "Passeio com a Nina no parque."),
            record("sample-r5", "2026-10-18", "21:00", "Conversa longa com a Ana sobre o ano que vem."),
        )
        for (month in 1..14) {
            val day = LocalDate.of(2026, 10, 19).minusMonths(month.toLong()).withDayOfMonth(12)
            ids += record("sample-h$month", day.toString(), "19:30", "Lembrança de $day com a Marina e a Nina.")
        }
        versionedRecord()
        addMentions()
        return ids
    }

    /** Links every sample record to the entities its text actually names. */
    private suspend fun addMentions() {
        // The same record repeats Ana twice: the composite key keeps one link.
        listOf("sample-ana", "sample-ana", "sample-marina").forEach { entityId ->
            entities.upsertLink(RecordEntityLink("sample-r1", entityId, "DECLARED", "CONFIRMED"))
        }
        val links = mapOf(
            "sample-r2" to listOf("sample-ana", "sample-curitiba"),
            "sample-r3" to listOf("sample-marina"),
            "sample-r4" to listOf("sample-nina", "sample-curitiba"),
            "sample-r5" to listOf("sample-ana"),
            "sample-v" to listOf("sample-marina"),
        )
        links.forEach { (recordId, entityIds) ->
            entityIds.forEach { entities.upsertLink(RecordEntityLink(recordId, it, "DECLARED", "CONFIRMED")) }
        }
        for (month in 1..14) {
            listOf("sample-marina", "sample-nina").forEach { entityId ->
                entities.upsertLink(RecordEntityLink("sample-h$month", entityId, "DECLARED", "CONFIRMED"))
            }
        }
    }

    private suspend fun record(
        id: String,
        day: String,
        time: String,
        text: String,
        audioId: String? = null,
    ): String {
        val moment = LocalDate.parse(day).atTime(LocalTime.parse(time))
            .atZone(ZoneId.systemDefault()).toInstant().toEpochMilli()
        records.insertRecord(RecordEntity(id, "$id-v1", moment, moment, "LOCAL", null, text.take(120)))
        records.insertVersion(RecordVersionEntity("$id-v1", id, 1, text, "USER", null, moment, true))
        records.insertMetadata(
            RecordMetadataEntity(id, day, null, audioId, null, "UNKNOWN", "DONE"),
        )
        return id
    }

    /** One record with three versions: the period count must stay at one. */
    private suspend fun versionedRecord() {
        val moment = LocalDate.of(2026, 10, 17).atTime(18, 0)
            .atZone(ZoneId.systemDefault()).toInstant().toEpochMilli()
        records.insertRecord(
            RecordEntity("sample-v", "sample-v-v3", moment, moment + 3_000, "LOCAL", null, "Versão final"),
        )
        listOf("Versão original", "Versão revisada", "Versão final").forEachIndexed { index, text ->
            records.insertVersion(
                RecordVersionEntity(
                    id = "sample-v-v${index + 1}",
                    recordId = "sample-v",
                    number = index + 1,
                    content = text,
                    origin = "USER",
                    baseVersionId = null,
                    createdAt = moment + index * 1_000L,
                    confirmed = true,
                ),
            )
        }
        records.insertMetadata(RecordMetadataEntity("sample-v", "2026-10-17", null, null, null, "UNKNOWN", "DONE"))
    }
}
