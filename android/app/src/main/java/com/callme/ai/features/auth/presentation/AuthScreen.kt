package com.callme.ai.features.auth.presentation

import android.content.Context
import android.net.Uri
import androidx.browser.customtabs.CustomTabsIntent
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.callme.ai.R
import com.callme.ai.core.ui.PillButton
import com.callme.ai.core.ui.Wordmark
import com.callme.ai.features.auth.domain.AuthState

/** Sign-in entry point: brand, the promise of the product and a single action. */
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
        modifier = Modifier.fillMaxSize().padding(horizontal = 32.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.Start,
    ) {
        Image(
            painter = painterResource(R.drawable.brand_mark),
            contentDescription = null,
            modifier = Modifier.size(96.dp),
        )
        Wordmark(Modifier.padding(top = 12.dp))
        Text(
            stringResource(R.string.auth_headline),
            style = MaterialTheme.typography.headlineLarge,
            modifier = Modifier.padding(top = 16.dp),
        )
        Text(
            stringResource(R.string.auth_body),
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(top = 16.dp),
        )
        if (state is AuthState.Loading) {
            CircularProgressIndicator(Modifier.padding(top = 32.dp))
        } else {
            PillButton(
                label = stringResource(R.string.auth_sign_in),
                onClick = { viewModel.startSignIn(provider) },
                modifier = Modifier.fillMaxWidth().padding(top = 32.dp),
            )
        }
        if (state is AuthState.Failed) {
            Text(
                stringResource(R.string.auth_error),
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.bodySmall,
                modifier = Modifier.padding(top = 16.dp),
            )
        }
    }
}

private fun Context.openBrowser(url: String) {
    CustomTabsIntent.Builder().build().launchUrl(this, Uri.parse(url))
}
