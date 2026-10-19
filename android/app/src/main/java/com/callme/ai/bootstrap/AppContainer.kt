package com.callme.ai.bootstrap

import android.content.Context
import com.callme.ai.BuildConfig
import com.callme.ai.core.database.DatabaseFactory
import com.callme.ai.core.network.ApiClient
import com.callme.ai.core.security.EncryptedFiles
import com.callme.ai.core.security.EncryptedSessionStore
import com.callme.ai.core.security.KeystoreCipherBox
import com.callme.ai.core.security.SecretFile
import com.callme.ai.features.auth.adapters.OidcAuthRepository
import com.callme.ai.features.capture.adapters.EncryptedRecordingStore
import com.callme.ai.features.capture.adapters.MediaRecorderAudioRecorder
import com.callme.ai.features.capture.adapters.SpeechRecognizerDictation
import com.callme.ai.features.capture.application.CaptureService
import com.callme.ai.features.auth.application.AuthRepository
import com.callme.ai.features.auth.application.DeviceIdStore
import com.callme.ai.features.records.adapters.RoomRecordsRepository
import com.callme.ai.features.records.application.RecordsRepository

/** Manual composition root. No reflection, no global singletons. */
class AppContainer(context: Context, provider: String = BuildConfig.OIDC_PROVIDER) {
    private val appContext = context.applicationContext

    val sessionStore = EncryptedSessionStore(
        appContext,
        KeystoreCipherBox(alias = "callme.session"),
    )

    private val api = ApiClient(sessionStore)
    private val deviceIds = DeviceIdStore(appContext)

    val authRepository: AuthRepository = OidcAuthRepository(
        api = api.authApi,
        sessionStore = sessionStore,
        deviceIds = deviceIds,
        redirectUri = BuildConfig.OIDC_REDIRECT_URI,
    )

    private val database = DatabaseFactory(
        appContext,
        SecretFile(appContext, "db.key", KeystoreCipherBox("callme.database")),
    ).open()

    val recordsRepository: RecordsRepository = RoomRecordsRepository(database.recordsDao())

    private val dictation = SpeechRecognizerDictation(appContext)
    val captureService: CaptureService = CaptureService(
        dictation = dictation,
        recorder = MediaRecorderAudioRecorder(appContext),
        recordings = EncryptedRecordingStore(appContext, database.recordsDao(), EncryptedFiles(appContext)),
    )

    val oidcProvider: String = provider
}
