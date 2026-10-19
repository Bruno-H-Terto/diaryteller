package com.callme.ai.features.records.presentation

/** First line of a record shown as the headline, with the remainder as body copy. */
internal data class DraftParts(val title: String, val body: String)

/** Splits a stored record into headline and body without losing the user's text. */
internal fun splitDraft(text: String): DraftParts {
    val content = text.trimStart('\n')
    val next = content.indexOf('\n')
    if (next < 0) return DraftParts(content, "")
    return DraftParts(content.substring(0, next), content.substring(next + 1).trimStart('\n'))
}

/** Rebuilds the stored record from the two fields, keeping the headline first. */
internal fun joinDraft(title: String, body: String): String = when {
    title.isEmpty() -> body
    body.isEmpty() -> title
    else -> "$title\n\n$body"
}
