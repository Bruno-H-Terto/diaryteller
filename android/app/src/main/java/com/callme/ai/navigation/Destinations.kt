package com.callme.ai.navigation

object Destinations {
    const val RECORDS = "records"
    const val CONVERSATION = "conversation"
    const val TIMELINE = "timeline"
    const val ACCOUNT = "account"
    const val EDITOR = "editor/{recordId}"
    const val VERSIONS = "versions/{recordId}"

    fun editor(recordId: String) = "editor/$recordId"
    fun versions(recordId: String) = "versions/$recordId"
}
