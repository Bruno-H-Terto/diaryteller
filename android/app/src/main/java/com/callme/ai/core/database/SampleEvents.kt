package com.callme.ai.core.database

/** Events and pending suggestions of the synthetic diary. */
internal suspend fun EntitiesDao.insertSampleEvents(recordIds: List<String>) {
    val rows = listOf(
        sampleEvent("sample-ev1", "Conversa com Ana", "Dois relatos do mesmo almoço.", "2026-10-18", "DAY", "CONFIRMED"),
        sampleEvent("sample-ev2", "Mudança para Curitiba", "Marina ajudou na mudança.", "2019-01-01", "YEAR", "SUGGESTED"),
        sampleEvent("sample-ev3", "Passeio com Nina", "Nina correu no parque.", "2026-10-18", "DAY", "CONFIRMED"),
        sampleEvent("sample-ev4", "Uma lembrança sem data", "Nenhuma data foi citada.", null, "UNKNOWN", "CONFIRMED"),
    )
    rows.forEach { upsertEvent(it) }
    addSources("sample-ev1", listOf(recordIds[1], recordIds[4]))
    addSources("sample-ev2", listOf(recordIds[1], recordIds[2]))
    addSources("sample-ev3", listOf(recordIds[3]))
    addSources("sample-ev4", listOf(recordIds[0]))
    addParticipants("sample-ev1", mapOf("sample-ana" to "PERSON", "sample-marina" to "PERSON"))
    addParticipants("sample-ev2", mapOf("sample-marina" to "PERSON", "sample-curitiba" to "PLACE"))
    addParticipants("sample-ev3", mapOf("sample-nina" to "ANIMAL", "sample-curitiba" to "PLACE"))
    addParticipants("sample-ev4", mapOf("sample-marina-vizinha" to "PERSON"))
    upsertRelationship(
        RelationshipEntity(
            id = "sample-rel-suggested",
            fromEntityId = "self",
            toEntityId = "sample-marina-vizinha",
            label = "Vizinha",
            origin = "SUGGESTED",
            reviewState = "SUGGESTED",
            sourceRecordId = recordIds.first(),
            createdAt = System.currentTimeMillis(),
        ),
    )
}

private fun sampleEvent(
    id: String,
    title: String,
    summary: String,
    date: String?,
    precision: String,
    state: String,
) = EventEntity(
    id = id,
    title = title,
    summary = summary,
    eventDate = date,
    datePrecision = precision,
    coverUri = null,
    origin = if (state == "SUGGESTED") "SUGGESTED" else "DECLARED",
    reviewState = state,
    updatedAt = System.currentTimeMillis(),
)

private suspend fun EntitiesDao.addSources(eventId: String, recordIds: List<String>) {
    recordIds.forEach { insertEventRecord(EventRecordLink(eventId, it)) }
}

private suspend fun EntitiesDao.addParticipants(eventId: String, people: Map<String, String>) {
    people.forEach { (entityId, role) -> insertEventEntity(EventEntityLink(eventId, entityId, role)) }
}

/** Entities, relations and mentions of the synthetic diary. */
internal suspend fun EntitiesDao.insertSampleEntities() {
    val rows = listOf(
        sampleEntity("sample-ana", "PERSON", "Ana", "p1", "Colega de trabalho", "DECLARED", "CONFIRMED"),
        sampleEntity("sample-marina", "PERSON", "Marina", "p2", "Sua irmã", "CONFIRMED", "CONFIRMED"),
        sampleEntity("sample-marina-vizinha", "PERSON", "Marina", "p3", "Vizinha", "DECLARED", "CONFIRMED"),
        sampleEntity("sample-nina", "ANIMAL", "Nina", "a1", "Sua cachorra", "CONFIRMED", "CONFIRMED"),
        sampleEntity("sample-curitiba", "PLACE", "Curitiba", "l1", "", "", ""),
    )
    rows.forEach { (row, relation) ->
        insert(row)
        relation?.let { upsertRelationship(it) }
    }
}

private fun sampleEntity(
    id: String,
    type: String,
    name: String,
    model: String,
    label: String,
    origin: String,
    review: String,
): Pair<DiaryEntity, RelationshipEntity?> = DiaryEntity(
    id = id,
    type = type,
    name = name,
    avatarModel = model,
    avatarBackground = 0xFFEAE5F6,
    skinColor = null,
    hairColor = null,
    clothingColor = null,
    createdAt = System.currentTimeMillis(),
    updatedAt = System.currentTimeMillis(),
) to if (label.isBlank()) {
    null
} else {
    RelationshipEntity(
        id = "self-$id",
        fromEntityId = "self",
        toEntityId = id,
        label = label,
        origin = origin,
        reviewState = review,
        sourceRecordId = null,
        createdAt = System.currentTimeMillis(),
    )
}
