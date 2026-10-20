package com.callme.ai.core.i18n

import android.app.Activity
import android.content.Context
import android.content.ContextWrapper
import android.content.res.Configuration
import com.callme.ai.R
import java.util.Locale

/**
 * Locale storage so a language catalogue becomes a selectable language.
 *
 * The list of languages comes from the generated `app_languages` resource, which
 * the catalogue build writes from the `android/i18n` catalogues. Reading and writing only
 * touches the app's private preferences file.
 */
class LocalePreference(context: Context) {

    private val preferences = context.applicationContext
        .getSharedPreferences(PREFERENCES, Context.MODE_PRIVATE)

    /** Stored language tag, or `null` while the device default is in use. */
    fun stored(): String? = preferences.getString(KEY_LANGUAGE, null)

    /** Persist the chosen tag; `null` goes back to following the device. */
    fun store(tag: String?) {
        preferences.edit().apply {
            if (tag == null) remove(KEY_LANGUAGE) else putString(KEY_LANGUAGE, tag)
        }.apply()
    }

    private companion object {
        const val PREFERENCES = "diaryteller.preferences"
        const val KEY_LANGUAGE = "language"
    }
}

/** One selectable catalogue, as written by the translation build. */
data class AppLanguage(val tag: String, val label: String)

/** Reads the generated catalogue list and applies the stored choice. */
object AppLanguages {

    /** Catalogue entries in build order; the first one is the default language. */
    fun available(context: Context): List<AppLanguage> =
        context.resources.getStringArray(R.array.app_languages).mapNotNull { entry ->
            val separator = entry.lastIndexOf('|')
            if (separator <= 0) {
                null
            } else {
                AppLanguage(entry.substring(separator + 1), entry.substring(0, separator))
            }
        }

    /** Tag currently applied: the stored choice, else the device language. */
    fun current(context: Context): String {
        val languages = available(context)
        LocalePreference(context).stored()?.let { stored ->
            if (languages.any { it.tag == stored }) return stored
        }
        val device = context.resources.configuration.locales[0]
        val match = languages.firstOrNull { Locale.forLanguageTag(it.tag).language == device.language }
        return match?.tag ?: languages.firstOrNull()?.tag.orEmpty()
    }

    /** Locale the activity must use; `null` keeps the device configuration. */
    fun resolve(context: Context): Locale? {
        val stored = LocalePreference(context).stored() ?: return null
        if (available(context).none { it.tag == stored }) return null
        return Locale.forLanguageTag(stored)
    }

    /** Base context carrying the chosen locale, used from `attachBaseContext`. */
    fun wrap(base: Context): Context {
        val locale = resolve(base) ?: return base
        val configuration = Configuration(base.resources.configuration)
        configuration.setLocale(locale)
        configuration.setLayoutDirection(locale)
        return base.createConfigurationContext(configuration)
    }
}

/** Persist a choice and recreate the activity so every screen re-reads the locale. */
fun changeLanguage(activity: Activity, tag: String) {
    LocalePreference(activity).store(tag)
    activity.recreate()
}

/** Unwraps the activity that hosts a composable, or `null` outside an activity. */
tailrec fun Context.findActivity(): Activity? = when (this) {
    is Activity -> this
    is ContextWrapper -> baseContext.findActivity()
    else -> null
}
