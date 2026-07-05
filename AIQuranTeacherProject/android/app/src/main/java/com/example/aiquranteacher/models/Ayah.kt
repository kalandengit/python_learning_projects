package com.example.aiquranteacher.models

data class Ayah(
    val id: Int,
    val surahId: Int,
    val number: Int,
    val text: String,
    val translation: String?,
    val referenceAudioUrl: String?,
    val userRecordingUrl: String?
)
