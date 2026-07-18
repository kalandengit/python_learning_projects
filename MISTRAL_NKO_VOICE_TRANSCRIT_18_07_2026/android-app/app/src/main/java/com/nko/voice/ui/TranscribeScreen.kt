package com.nko.voice.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nko.voice.api.ApiClient
import com.nko.voice.api.TokenStore
import com.nko.voice.audio.AudioRecorder
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

@Composable
fun TranscribeScreen() {
    val context = LocalContext.current
    val recorder = remember { AudioRecorder(context) }
    val api = remember { ApiClient(TokenStore(context)) }
    val scope = rememberCoroutineScope()

    var recording by remember { mutableStateOf(false) }
    var busy by remember { mutableStateOf(false) }
    var latin by remember { mutableStateOf("") }
    var nko by remember { mutableStateOf("") }
    var error by remember { mutableStateOf<String?>(null) }

    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text("ߒߞߏ N'Ko Voice", style = MaterialTheme.typography.headlineSmall)

        Button(
            modifier = Modifier.fillMaxWidth(),
            enabled = !busy,
            onClick = {
                if (!recording) {
                    error = null
                    recording = recorder.start()
                    if (!recording) error = "Could not start recording"
                } else {
                    recording = false
                    val file = recorder.stop() ?: return@Button
                    busy = true
                    scope.launch {
                        try {
                            val result = withContext(Dispatchers.IO) {
                                api.transcribe(file, language = "bam")
                            }
                            latin = result.latinText
                            nko = result.nkoText
                        } catch (e: Exception) {
                            error = e.message
                        } finally {
                            recorder.discard(file) // audio never persists on device
                            busy = false
                        }
                    }
                }
            },
        ) {
            Text(if (recording) "■ Stop" else "● Record")
        }

        if (busy) CircularProgressIndicator()
        error?.let { Text(it, color = MaterialTheme.colorScheme.error) }

        if (latin.isNotEmpty()) {
            Text("Latin", style = MaterialTheme.typography.labelLarge)
            Text(latin)
        }
        if (nko.isNotEmpty()) {
            Text("N'Ko", style = MaterialTheme.typography.labelLarge)
            // RTL rendering for N'Ko script.
            androidx.compose.runtime.CompositionLocalProvider(
                androidx.compose.ui.platform.LocalLayoutDirection provides LayoutDirection.Rtl
            ) {
                Text(
                    nko,
                    fontSize = 26.sp,
                    textAlign = TextAlign.Right,
                    modifier = Modifier.fillMaxWidth(),
                )
            }
        }
    }
}
