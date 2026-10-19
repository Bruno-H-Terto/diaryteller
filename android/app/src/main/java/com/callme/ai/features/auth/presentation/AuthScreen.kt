package com.callme.ai.features.auth.presentation

import android.content.Context
import android.net.Uri
import androidx.browser.customtabs.CustomTabsIntent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.callme.ai.R
import com.callme.ai.features.auth.domain.AuthState

@Composable
fun AuthScreen(viewModel: AuthViewModel, provider: String) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val launchUrl by viewModel.launchUrl.collectAsStateWithLifecycle()
    val context = LocalContext.current

    LaunchedEffect(launchUrl) {
        launchUrl?.let {
            context.openBrowser(it)
            viewModel.consumeLaunchUrl()
        }
    }

    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(stringResource(R.string.auth_title), style = MaterialTheme.typography.headlineMedium)
        Text(
            stringResource(R.string.auth_body),
            style = MaterialTheme.typography.bodyMedium,
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(vertical = 16.dp),
        )
        if (state is AuthState.Loading) {
            CircularProgressIndicator()
            return@Column
        }
        Button(onClick = { viewModel.startSignIn(provider) }, enabled = state !is AuthState.Loading) {
            Text(stringResource(R.string.auth_sign_in))
        }
        if (state is AuthState.Failed) {
            Text(
                stringResource(R.string.auth_error),
                color = MaterialTheme.colorScheme.error,
                modifier = Modifier.padding(top = 16.dp),
            )
        }
    }
}

private fun Context.openBrowser(url: String) {
    CustomTabsIntent.Builder().build().launchUrl(this, Uri.parse(url))
}
