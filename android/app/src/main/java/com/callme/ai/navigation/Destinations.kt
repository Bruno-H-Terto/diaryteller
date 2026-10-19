package com.callme.ai.navigation

/** Navigation graph of the app: three destinations plus full-screen editors. */
object Destinations {
    const val DIARY = "diario"
    const val CONVERSATIONS = "conversas"
    const val SETTINGS = "ajustes"
    const val PRIVACY = "ajustes/privacidade"
    const val ACCOUNT = "ajustes/conta"
    const val EDITOR = "editor/{recordId}"
    const val VERSIONS = "versions/{recordId}"
    const val CAPTURE = "capture/{mode}"

    fun editor(recordId: String) = "editor/$recordId"
    fun versions(recordId: String) = "versions/$recordId"
    fun capture(mode: String) = "capture/$mode"
}
