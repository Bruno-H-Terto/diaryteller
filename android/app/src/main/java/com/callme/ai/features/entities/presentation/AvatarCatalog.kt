package com.callme.ai.features.entities.presentation

import com.callme.ai.core.model.AvatarStyle
import com.callme.ai.features.entities.domain.EntityType

/** Preset models and colours offered by the avatar editor. */
object AvatarCatalog {
    val backgrounds = listOf(
        0xFFEAE5F6, 0xFFF7D9C4, 0xFFDCEBE3, 0xFFF6E4DA, 0xFFE4E8F6, 0xFFF5E9C8,
    )
    val skins = listOf(0xFFF3D3B5, 0xFFE8C39E, 0xFFC98E63, 0xFF9A6440, 0xFF6B4429)
    val hairs = listOf(0xFF3B2E2A, 0xFF6B4429, 0xFFB9793A, 0xFF2B2938, 0xFF8E8E93)
    val clothing = listOf(0xFF51438F, 0xFFB86443, 0xFF4F7D6B, 0xFF8A6A4B, 0xFF686477)

    fun models(type: EntityType): List<String> = when (type) {
        EntityType.PERSON, EntityType.SELF -> listOf("p1", "p2", "p3", "p4")
        EntityType.ANIMAL -> listOf("a1", "a2")
        EntityType.PLACE -> listOf("l1", "l2")
        EntityType.EVENT -> listOf("e1")
    }

    /** Only people expose skin, hair and clothing choices. */
    fun editableParts(type: EntityType): Boolean =
        type == EntityType.PERSON || type == EntityType.SELF

    fun styleFor(type: EntityType, model: String, background: Long) = AvatarStyle(
        model = model,
        background = background,
        skin = if (editableParts(type)) skins[1] else null,
        hair = if (editableParts(type)) hairs[0] else null,
        clothing = if (editableParts(type)) clothing[0] else null,
    )
}
