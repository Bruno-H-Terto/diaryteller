package com.callme.ai.features.capture.adapters

import android.content.Context
import com.callme.ai.core.database.RecordsDao
import com.callme.ai.core.database.RecordingEntity
import com.callme.ai.core.security.EncryptedFiles
import com.callme.ai.features.capture.application.RecordingStore
import com.callme.ai.features.capture.domain.LocalRecording
import java.io.File
import java.util.UUID
import kotlinx.coroutines.runBlocking

/**
 * Voice notes are encrypted with a Keystore-backed key, stored in app-private
 * files and never uploaded. Playback decrypts to a cache file that is removed
 * when the app releases it.
 */
class EncryptedRecordingStore(
    private val context: Context,
    private val dao: RecordsDao,
    private val files: EncryptedFiles,
    private val newId: () -> String = { UUID.randomUUID().toString() },
    private val now: () -> Long = { System.currentTimeMillis() },
) : RecordingStore {

    private val directory = File(context.filesDir, "recordings")

    override fun save(temporaryFile: File, durationMs: Long): LocalRecording {
        val id = newId()
        val target = File(directory, "$id.enc")
        files.copyInto(temporaryFile, target)
        temporaryFile.delete()
        val entity = RecordingEntity(
            id = id,
            createdAt = now(),
            durationMs = durationMs,
            sizeBytes = target.length(),
            fileName = target.name,
            state = "STORED",
            recordId = null,
        )
        runBlocking { dao.insertRecording(entity) }
        return LocalRecording(id, entity.createdAt, durationMs, entity.sizeBytes, null)
    }

    override fun list(): List<LocalRecording> = runBlocking {
        dao.recordings().map {
            LocalRecording(it.id, it.createdAt, it.durationMs, it.sizeBytes, it.recordId)
        }
    }

    override fun delete(id: String) {
        runBlocking {
            dao.recording(id)?.let { File(directory, it.fileName).delete() }
            dao.deleteRecording(id)
        }
    }

    override fun materialize(id: String): File? = runBlocking {
        val stored = dao.recording(id) ?: return@runBlocking null
        val source = File(directory, stored.fileName)
        if (!source.exists()) return@runBlocking null
        val playback = File(context.cacheDir, "playback-$id.m4a")
        files.copyOut(source, playback)
        playback
    }
}
