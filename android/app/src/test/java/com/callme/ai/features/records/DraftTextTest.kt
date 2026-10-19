package com.callme.ai.features.records

import com.callme.ai.features.records.presentation.joinDraft
import com.callme.ai.features.records.presentation.splitDraft
import org.junit.Assert.assertEquals
import org.junit.Test

class DraftTextTest {
    @Test
    fun `single line becomes only a title`() {
        val parts = splitDraft("Começar pelo que importa")

        assertEquals("Começar pelo que importa", parts.title)
        assertEquals("", parts.body)
    }

    @Test
    fun `second line becomes the body`() {
        val parts = splitDraft("Título\nCorpo do registro")

        assertEquals("Título", parts.title)
        assertEquals("Corpo do registro", parts.body)
    }

    @Test
    fun `blank line after the title is skipped`() {
        val parts = splitDraft("Título\n\nPrimeiro parágrafo\nsegunda linha")

        assertEquals("Título", parts.title)
        assertEquals("Primeiro parágrafo\nsegunda linha", parts.body)
    }

    @Test
    fun `joining keeps a single separator between title and body`() {
        assertEquals("Título\n\nCorpo", joinDraft("Título", "Corpo"))
        assertEquals("Título", joinDraft("Título", ""))
        assertEquals("Corpo", joinDraft("", "Corpo"))
    }

    @Test
    fun `round trip preserves the stored text`() {
        val original = "Título\n\nCorpo"
        val parts = splitDraft(original)

        assertEquals(original, joinDraft(parts.title, parts.body))
    }
}
