package com.callme.ai.features.capture.adapters

import android.content.Context
import java.io.File
import org.vosk.Model

/**
 * Unpacks and holds the speech model that ships inside the app.
 *
 * The model is copied from the assets into app storage once per version, on a
 * background thread, and reused for the whole process. Because it travels with
 * the app, recognition never depends on a language pack downloaded from the
 * system and no audio leaves the phone.
 */
class VoskModel(private val context: Context, private val asset: String = ASSET) {

    @Volatile
    private var model: Model? = null

    @Volatile
    private var failure: String? = null

    private val lock = Object()

    /** Waits for the model, unpacking it on first use; null when it cannot load. */
    fun await(): Model? {
        model?.let { return it }
        synchronized(lock) {
            model?.let { return it }
            if (failure != null) return null
            val directory = runCatching { unpack() }.getOrElse { error ->
                failure = error.message ?: "model unavailable"
                return null
            }
            val created = runCatching { Model(directory.absolutePath) }.getOrElse { error ->
                failure = error.message ?: "model invalid"
                return null
            }
            model = created
            return created
        }
    }

    /** True when the model is unpacked and usable. */
    fun available(): Boolean = await() != null

    /** Reason the model could not be loaded, for logs and the studio panel. */
    fun failure(): String? = failure

    fun release() {
        model?.close()
        model = null
    }

    /** Copies `assets/<asset>` into `files/<asset>` when the version changed. */
    private fun unpack(): File {
        val target = File(context.filesDir, asset)
        val marker = File(target, VERSION_FILE)
        if (marker.isFile && marker.readText() == VERSION) return target
        if (target.exists()) target.deleteRecursively()
        copy(asset, target)
        marker.writeText(VERSION)
        return target
    }

    private fun copy(assetPath: String, target: File) {
        val children = context.assets.list(assetPath).orEmpty()
        if (children.isEmpty()) {
            target.parentFile?.mkdirs()
            context.assets.open(assetPath).use { input ->
                target.outputStream().use { output -> input.copyTo(output, BUFFER) }
            }
            return
        }
        target.mkdirs()
        children.forEach { child -> copy("$assetPath/$child", File(target, child)) }
    }

    private companion object {
        const val ASSET = "model-pt"
        const val VERSION = "pt-0.3"
        const val VERSION_FILE = ".unpacked"
        const val BUFFER = 64 * 1024
    }
}
