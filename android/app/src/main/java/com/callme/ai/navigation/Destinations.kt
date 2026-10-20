package com.callme.ai.navigation

/** Navigation graph: four destinations plus full-screen editors and details. */
object Destinations {
    const val DIARY = "diario"
    const val CONNECTIONS = "conexoes"
    const val CONVERSATIONS = "conversas"
    const val SETTINGS = "ajustes"
    const val PRIVACY = "ajustes/privacidade"
    const val ACCOUNT = "ajustes/conta"
    const val EDITOR = "editor/{recordId}"
    const val VERSIONS = "versions/{recordId}"
    const val CAPTURE = "capture/{mode}"
    const val ENTITIES = "conexoes/pessoas"
    const val ENTITY = "conexoes/pessoa/{entityId}?mes={mes}"
    const val AVATAR = "conexoes/pessoa/{entityId}/avatar"
    const val EVENT = "conexoes/acontecimento/{eventId}"

    fun editor(recordId: String) = "editor/$recordId"
    fun versions(recordId: String) = "versions/$recordId"
    fun capture(mode: String) = "capture/$mode"
    fun entity(entityId: String, month: String = "") = "conexoes/pessoa/$entityId?mes=$month"
    fun avatar(entityId: String) = "conexoes/pessoa/$entityId/avatar"
    fun event(eventId: String) = "conexoes/acontecimento/$eventId"
}
