package com.callme.ai.navigation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider

/** Builds a single view model without a DI framework. */
internal fun <T : ViewModel> factory(create: () -> T): ViewModelProvider.Factory =
    object : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <V : ViewModel> create(modelClass: Class<V>): V = create() as V
    }
