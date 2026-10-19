package com.callme.ai.features.records

import com.callme.ai.features.records.domain.RecordVersion
import com.callme.ai.features.records.domain.VersionOrigin
import com.callme.ai.features.records.domain.Versioning
import com.google.common.truth.Truth.assertThat
import org.junit.Test

class VersioningTest {

    private fun version(number: Int, content: String = "v$number") = RecordVersion(
        id = "id-$number",
        recordId = "record",
        number = number,
        content = content,
        origin = VersionOrigin.USER,
        baseVersionId = if (number == 1) null else "id-${number - 1}",
        createdAt = number.toLong(),
        confirmed = true,
    )

    @Test
    fun `first version is one and next follows the highest number`() {
        assertThat(Versioning.nextNumber(emptyList())).isEqualTo(1)
        assertThat(Versioning.nextNumber(listOf(version(1), version(2)))).isEqualTo(3)
        assertThat(Versioning.nextNumber(listOf(version(1), version(3)))).isEqualTo(4)
    }

    @Test
    fun `restore copies content but starts a new provenance chain`() {
        val target = version(2, "texto original")
        val restored = Versioning.restored(target, baseVersionId = "current", id = "new", now = 99)
        assertThat(restored.content).isEqualTo("texto original")
        assertThat(restored.origin).isEqualTo(VersionOrigin.RESTORE)
        assertThat(restored.baseVersionId).isEqualTo("current")
        assertThat(restored.id).isEqualTo("new")
        assertThat(restored.confirmed).isTrue()
        assertThat(target.number).isEqualTo(2)
    }
}
