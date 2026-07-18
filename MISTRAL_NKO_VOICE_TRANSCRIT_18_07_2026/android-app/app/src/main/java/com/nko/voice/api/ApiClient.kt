package com.nko.voice.api

import com.nko.voice.BuildConfig
import java.io.File
import java.io.IOException
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

data class TranscriptionResult(
    val latinText: String,
    val nkoText: String,
    val engine: String,
    val durationMs: Long,
)

class ApiClient(
    private val tokens: TokenStore? = null,
    private val baseUrl: String = BuildConfig.API_BASE_URL,
) {
    private val http = OkHttpClient()

    fun login(email: String, password: String) {
        val body = JSONObject().put("email", email).put("password", password)
        val request = Request.Builder()
            .url("$baseUrl/api/v1/auth/login")
            .post(body.toString().toRequestBody("application/json".toMediaType()))
            .build()
        http.newCall(request).execute().use { response ->
            if (!response.isSuccessful) throw IOException("Login failed: ${response.code}")
            val json = JSONObject(response.body!!.string())
            tokens?.accessToken = json.getString("access_token")
            tokens?.refreshToken = json.getString("refresh_token")
        }
    }

    fun transcribe(
        audio: File,
        language: String = "bam",
        engine: String? = null,
        storeHistory: Boolean = false,
    ): TranscriptionResult {
        val multipart = MultipartBody.Builder().setType(MultipartBody.FORM)
            .addFormDataPart(
                "audio", audio.name,
                audio.asRequestBody("audio/mp4".toMediaType()),
            )
            .addFormDataPart("language", language)
            .addFormDataPart("store_history", storeHistory.toString())
            .apply { engine?.let { addFormDataPart("asr_engine", it) } }
            .build()
        val builder = Request.Builder()
            .url("$baseUrl/api/v1/transcriptions/upload")
            .post(multipart)
        tokens?.accessToken?.let { builder.header("Authorization", "Bearer $it") }
        http.newCall(builder.build()).execute().use { response ->
            if (!response.isSuccessful) throw IOException("Transcription failed: ${response.code}")
            return parseTranscription(response.body!!.string())
        }
    }

    companion object {
        fun parseTranscription(payload: String): TranscriptionResult {
            val json = JSONObject(payload)
            return TranscriptionResult(
                latinText = json.getString("latin_text"),
                nkoText = json.getString("nko_text"),
                engine = json.getString("asr_engine"),
                durationMs = json.optLong("duration_ms"),
            )
        }
    }
}
