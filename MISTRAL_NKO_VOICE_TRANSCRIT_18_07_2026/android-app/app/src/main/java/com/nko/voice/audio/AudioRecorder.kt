package com.nko.voice.audio

import android.content.Context
import android.media.MediaRecorder
import android.os.Build
import java.io.File

/**
 * Records microphone audio to an in-app-cache M4A (AAC) file.
 * 16 kHz mono keeps uploads small and matches the backend's ASR input.
 * The file lives in cacheDir only and is deleted after upload.
 */
class AudioRecorder(private val context: Context) {

    private var recorder: MediaRecorder? = null
    private var output: File? = null

    fun start(): Boolean {
        val file = File.createTempFile("nko-rec", ".m4a", context.cacheDir)
        val mediaRecorder =
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) MediaRecorder(context)
            else @Suppress("DEPRECATION") MediaRecorder()
        return try {
            mediaRecorder.apply {
                setAudioSource(MediaRecorder.AudioSource.MIC)
                setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
                setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
                setAudioSamplingRate(16_000)
                setAudioChannels(1)
                setAudioEncodingBitRate(48_000)
                setOutputFile(file.absolutePath)
                prepare()
                start()
            }
            recorder = mediaRecorder
            output = file
            true
        } catch (e: Exception) {
            mediaRecorder.release()
            file.delete()
            false
        }
    }

    /** Stops recording and returns the audio file, or null on failure. */
    fun stop(): File? {
        val mediaRecorder = recorder ?: return null
        recorder = null
        return try {
            mediaRecorder.stop()
            output
        } catch (e: Exception) {
            output?.delete()
            null
        } finally {
            mediaRecorder.release()
        }
    }

    fun discard(file: File?) {
        file?.delete()
    }
}
