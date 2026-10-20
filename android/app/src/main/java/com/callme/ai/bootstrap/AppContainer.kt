package com.callme.ai.bootstrap

import android.content.Context
import com.callme.ai.BuildConfig
import com.callme.ai.core.database.DatabaseFactory
import com.callme.ai.core.database.SampleDiary
import com.callme.ai.core.network.ApiClient
import com.callme.ai.core.network.SessionRefresher
import com.callme.ai.core.security.EncryptedFiles
import com.callme.ai.core.security.EncryptedSessionStore
import com.callme.ai.core.security.KeystoreCipherBox
import com.callme.ai.core.security.SecretFile
import com.callme.ai.features.auth.adapters.OidcAuthRepository
import com.callme.ai.core.i18n.AppLanguages
import com.callme.ai.core.media.MediaStore
import com.callme.ai.features.capture.adapters.MediaRecorderAudioRecorder
import com.callme.ai.features.capture.adapters.MediaRecordingStore
import com.callme.ai.features.capture.application.DictationEngine
import com.callme.ai.features.capture.adapters.VoskDictation
import com.callme.ai.features.capture.adapters.VoskFileTranscriber
import com.callme.ai.features.capture.adapters.VoskModel
import com.callme.ai.features.capture.application.CaptureService
import com.callme.ai.features.conversations.adapters.AndroidReplySpeaker
import com.callme.ai.features.conversations.adapters.HttpConversationRepository
import com.callme.ai.features.conversations.adapters.RoomDiaryMutator
import com.callme.ai.features.conversations.application.DiaryMutator
import com.callme.ai.features.conversations.application.ReplySpeaker
import com.callme.ai.features.conversations.application.ConversationRepository
import com.callme.ai.features.connections.adapters.RoomConnectionsRepository
import com.callme.ai.features.connections.application.ConnectionsRepository
import com.callme.ai.features.entities.adapters.RoomEntitiesRepository
import com.callme.ai.features.entities.application.EntitiesRepository
import com.callme.ai.features.auth.application.AuthRepository
import com.callme.ai.features.auth.application.DeviceIdStore
import com.callme.ai.features.records.adapters.RoomRecordsRepository
import com.callme.ai.features.records.application.RecordsRepository
import java.util.Locale
import kotlinx.coroutines.runBlocking

/** Manual composition root. No reflection, no global singletons. */
class AppContainer(context: Context, provider: String = BuildConfig.OIDC_PROVIDER) {
    private val appContext = context.applicationContext

    val sessionStore = EncryptedSessionStore(
        appContext,
        KeystoreCipherBox(alias = "callme.session"),
    )

    private val api = ApiClient(sessionStore)
    private val deviceIds = DeviceIdStore(appContext)

    init {
        api.refresher = SessionRefresher(sessionStore, api.refreshClient(), runBlocking { deviceIds.get() })
    }

    val authRepository: AuthRepository = OidcAuthRepository(
        api = api.authApi,
        sessionStore = sessionStore,
        deviceIds = deviceIds,
        redirectUri = BuildConfig.OIDC_REDIRECT_URI,
    )

    private val files = EncryptedFiles(appContext)

    val database = DatabaseFactory(
        appContext,
        SecretFile(appContext, "db.key", KeystoreCipherBox("callme.database")),
    ).open()

    val recordsRepository: RecordsRepository = RoomRecordsRepository(database.recordsDao())

    val media = MediaStore(appContext, database.recordsDao(), files)

    val sampleDiary = SampleDiary(database.recordsDao(), database.entitiesDao(), media)

    val entitiesRepository: EntitiesRepository = RoomEntitiesRepository(database.entitiesDao())
    val connectionsRepository: ConnectionsRepository =
        RoomConnectionsRepository(database.connectionsDao(), database.entitiesDao())

    init {
        runBlocking { entitiesRepository.ensureSelf() }
    }

    val diaryMutator: DiaryMutator = RoomDiaryMutator(
        dao = database.entitiesDao(),
        snapshotDao = database.snapshotDao(),
    )

    val conversationRepository: ConversationRepository = HttpConversationRepository(
        api = api.conversationApi,
        records = recordsRepository,
        mutator = diaryMutator,
    )

    /** Device synthesizer used to read answers aloud in the voice conversation. */
    fun replySpeaker(): ReplySpeaker =
        AndroidReplySpeaker(appContext, AppLanguages.resolve(appContext) ?: Locale.getDefault())

    val speechModel = VoskModel(appContext)

    /**
     * Speech input for the whole app.
     *
     * Debug builds replace it with the studio replay engine, so the voice loop
     * can be rehearsed on machines without a microphone.
     */
    var dictation: DictationEngine = VoskDictation(speechModel)

    /** Transcribes a recorded file with the same on-device model. */
    val fileTranscriber = VoskFileTranscriber(speechModel)

    /** Turns a stored voice note into text without leaving the device. */
    suspend fun transcribeRecording(recordingId: String): String? {
        val file = media.playable(recordingId) ?: return null
        return fileTranscriber.transcribe(file)
    }
    val captureService: CaptureService = CaptureService(
        dictation = dictation,
        recorder = MediaRecorderAudioRecorder(appContext),
        recordings = MediaRecordingStore(media),
    )

    val oidcProvider: String = provider
}
