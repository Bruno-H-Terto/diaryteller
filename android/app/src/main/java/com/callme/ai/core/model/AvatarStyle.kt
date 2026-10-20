package com.callme.ai.core.model

/**
 * Visual identity of one entity, chosen by the user and stored with it.
 *
 * [model] selects one of the drawn presets ("p1" person, "a1" animal, "l1"
 * place, "e1" date). Colours are ARGB values; changing them never creates a new
 * entity, so links and mentions stay attached.
 */
data class AvatarStyle(
    val model: String,
    val background: Long,
    val skin: Long? = null,
    val hair: Long? = null,
    val clothing: Long? = null,
)
