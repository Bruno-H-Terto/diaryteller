package com.callme.ai

import android.app.Application

/** Robolectric application that avoids the Keystore-backed production container. */
class TestApplication : Application()
