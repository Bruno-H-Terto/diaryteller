package com.callme.ai.features.capture.adapters

import com.callme.ai.core.media.MediaStore
import com.callme.ai.features.capture.application.RecordingStore
import com.callme.ai.features.capture.domain.LocalRecording
import java.io.File
import kotlinx.coroutines.runBlocking

/**
 * Adapter that lets the capture flow use the same encrypted media store as the
 * diary, so a voice note has exactly one owner and one playback path.
 */
class MediaRecordingStore(private val media: MediaStore) : RecordingStore {

    override fun save(temporaryFile: File, durationMs: Long): LocalRecording = runBlocking {
        val choice = media.saveRecording(temporaryFile, durationMs)
        LocalRecording(choice.id, choice.createdAt, choice.durationMs, temporaryFile.length(), null)
    }

    override fun list(): List<LocalRecording> = runBlocking {
        media.audioChoices().map { LocalRecording(it.id, it.createdAt, it.durationMs, 0, null) }
    }

    override fun delete(id: String) = runBlocking { media.deleteRecording(id) }

    override fun materialize(id: String): File? = runBlocking { media.playable(id) }
}
