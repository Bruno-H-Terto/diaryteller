package com.callme.ai.core.database

import android.content.Context
import androidx.room.Room
import com.callme.ai.core.security.SecretFile
import net.zetetic.database.sqlcipher.SupportOpenHelperFactory

/**
 * Room over SQLCipher. The passphrase is random per install, protected by the
 * Keystore and never derived from user data.
 */
class DatabaseFactory(private val context: Context, private val secretFile: SecretFile) {

    init {
        System.loadLibrary("sqlcipher")
    }

    fun open(): CallMeDatabase {
        val passphrase = secretFile.getOrCreate()
        val factory = SupportOpenHelperFactory(passphrase)
        return Room.databaseBuilder(context, CallMeDatabase::class.java, "callme.db")
            .openHelperFactory(factory)
            .build()
    }
}
