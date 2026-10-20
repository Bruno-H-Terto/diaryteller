package com.callme.ai.core.media

import androidx.compose.runtime.compositionLocalOf

/** Media access for UI: provided once by the composition root. */
val LocalMedia = compositionLocalOf<MediaStore> { error("MediaStore was not provided") }
