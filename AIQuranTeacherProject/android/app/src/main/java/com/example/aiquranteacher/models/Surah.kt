package com.example.aiquranteacher.models

data class Surah(
    val id: Int,
    val name: String,
    val arabicName: String,
    val ayahs: List<Ayah>,
    val translation: String?
)
