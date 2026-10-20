package com.callme.ai.core.media

import android.content.Context
import android.graphics.BitmapFactory
import android.net.Uri
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import com.callme.ai.core.database.RecordsDao
import com.callme.ai.core.security.EncryptedFiles
import java.io.File
import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/** A voice note the user can attach to a narration. */
data class AudioChoice(val id: String, val createdAt: Long, val durationMs: Long)

/**
 * Encrypted media owned by the diary: optional covers and voice notes. Files
 * never leave the app sandbox; playback and thumbnails decrypt on demand.
 */
class MediaStore(
    private val context: Context,
    private val dao: RecordsDao,
    private val files: EncryptedFiles,
    private val newId: () -> String = { UUID.randomUUID().toString() },
) {
    private val covers = File(context.filesDir, "covers")
    private val recordings = File(context.filesDir, "recordings")

    /** Copies the chosen image into private storage and points the record at it. */
    suspend fun attachCover(recordId: String, uri: Uri) = withContext(Dispatchers.IO) {
        covers.mkdirs()
        val name = "${newId()}.enc"
        val target = File(covers, name)
        val input = context.contentResolver.openInputStream(uri) ?: return@withContext
        input.use { source -> files.write(target).use { output -> source.copyTo(output) } }
        val previous = dao.metadata(recordId)?.coverUri
        dao.updateCover(recordId, name)
        previous?.let { File(covers, it).delete() }
    }

    suspend fun removeCover(recordId: String) = withContext(Dispatchers.IO) {
        val previous = dao.metadata(recordId)?.coverUri ?: return@withContext
        File(covers, previous).delete()
        dao.updateCover(recordId, null)
    }

    /** Decodes a stored cover without writing a plain copy to disk. */
    suspend fun cover(name: String?): ImageBitmap? = withContext(Dispatchers.IO) {
        if (name == null) return@withContext null
        val source = File(covers, name)
        if (!source.exists()) return@withContext null
        runCatching {
            files.read(source).use { stream ->
                BitmapFactory.decodeStream(stream)?.asImageBitmap()
            }
        }.getOrNull()
    }

    suspend fun audioChoices(): List<AudioChoice> = withContext(Dispatchers.IO) {
        dao.recordings().map { AudioChoice(it.id, it.createdAt, it.durationMs) }
    }

    /** Encrypts a finished recording into app-private storage. */
    suspend fun saveRecording(temporary: File, durationMs: Long): AudioChoice = withContext(Dispatchers.IO) {
        recordings.mkdirs()
        val id = newId()
        val target = File(recordings, "$id.enc")
        files.copyInto(temporary, target)
        temporary.delete()
        dao.insertRecording(
            com.callme.ai.core.database.RecordingEntity(
                id = id,
                createdAt = System.currentTimeMillis(),
                durationMs = durationMs,
                sizeBytes = target.length(),
                fileName = target.name,
                state = "STORED",
                recordId = null,
            ),
        )
        AudioChoice(id, System.currentTimeMillis(), durationMs)
    }

    suspend fun deleteRecording(id: String) = withContext(Dispatchers.IO) {
        dao.recording(id)?.let { File(recordings, it.fileName).delete() }
        dao.deleteRecording(id)
    }

    suspend fun attachAudio(recordId: String, recordingId: String?) = withContext(Dispatchers.IO) {
        dao.updateRecording(recordId, recordingId)
        recordingId?.let { dao.attachRecording(it, recordId) }
    }

    /** Decrypts a voice note to the cache so the platform player can read it. */
    suspend fun playable(recordingId: String): File? = withContext(Dispatchers.IO) {
        val stored = dao.recording(recordingId) ?: return@withContext null
        val source = File(recordings, stored.fileName)
        if (!source.exists()) return@withContext null
        val playback = File(context.cacheDir, "playback-$recordingId.m4a")
        files.copyOut(source, playback)
        playback
    }

    suspend fun durationOf(recordingId: String): Long? = withContext(Dispatchers.IO) {
        dao.recording(recordingId)?.durationMs
    }
}
